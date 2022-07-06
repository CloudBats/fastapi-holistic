from dataclasses import asdict, dataclass, field
import enum
from typing import Callable, Collection, NamedTuple, Optional, Type, TypeVar, Union

from alembic.config import Config
from alembic.operations.ops import OpContainer
import sqlalchemy as sa
from sqlalchemy import engine_from_config, MetaData, pool
from sqlalchemy.engine import Engine


T = TypeVar("T")


@dataclass
class DiffDepth1:
    lhs_only: set[T] = field(default_factory=set)
    rhs_only: set[T] = field(default_factory=set)


@dataclass
class DiffDepth2:
    lhs_only_items: dict[str, set[T]] = field(default_factory=dict)
    lhs_only_subitems: dict[str, set[T]] = field(default_factory=dict)
    rhs_only_items: dict[str, set[T]] = field(default_factory=dict)
    rhs_only_subitems: dict[str, set[T]] = field(default_factory=dict)


@dataclass
class EnumToColumnsMap:
    name: str
    kind: Union[Type[enum.Enum], sa.Enum]
    members: set[str]
    columns_by_table: dict[str, list[str]] = field(default_factory=dict)
    member_removal_rules: dict[str, str] = field(default_factory=dict)

    def add_column(self, table_name: str, column_name: str) -> None:
        # we're not using defaultdict due to a known bug related to dataclasses asdict
        try:
            self.columns_by_table[table_name].append(column_name)
        except KeyError:
            self.columns_by_table[table_name] = [column_name]

    def diff(self, other: "EnumToColumnsMap") -> DiffDepth1:
        return DiffDepth1(set(self.members) - set(other.members), set(other.members) - set(self.members))


@dataclass
class EnumToColumnsMapCollection:
    items: dict[str, EnumToColumnsMap]

    @classmethod
    def from_metadata(cls, metadata: MetaData) -> "EnumToColumnsMapCollection":
        result = dict()
        for table_name, table_contents in metadata.tables.items():
            for column in table_contents.columns:
                if isinstance(column.type, sa.Enum):
                    column_type_name = column.type.name
                    if not result.get(column_type_name):
                        if issubclass(k := column.type.python_type, enum.Enum):
                            kind = k
                            members = set(k._member_names_)
                        elif isinstance((k := column.type), sa.Enum):
                            kind = k
                            members = set(k.enums)
                        else:
                            raise TypeError(f"Unknown Enum class {column.type} encountered.")

                        result[column_type_name] = EnumToColumnsMap(
                            name=column_type_name,
                            kind=kind,
                            members=members,
                            member_removal_rules=getattr(
                                column.type.python_type, "member_removal_db_migration_rules", dict()
                            ),
                        )
                    result[column_type_name].add_column(table_name, column.name)

        return cls(result)

    def names_diff(self, other: "EnumToColumnsMapCollection") -> DiffDepth1:
        return DiffDepth1(set(self.items) - set(other.items), set(other.items) - set(self.items))

    def members_by_name_diff(self, other: "EnumToColumnsMapCollection") -> DiffDepth2:
        names_diff = self.names_diff(other)
        shared_names = set(self.items) & set(other.items)

        lhs_only_items = self.members_by_name(key=lambda name: name in names_diff.lhs_only)
        rhs_only_items = other.members_by_name(key=lambda name: name in names_diff.rhs_only)
        lhs_only_subitems = {}
        rhs_only_subitems = {}

        for name in shared_names:
            members_diff = self.items[name].diff(other.items[name])
            if members := members_diff.lhs_only:
                lhs_only_subitems |= {name: members}
            if members := members_diff.rhs_only:
                rhs_only_subitems |= {name: members}

        return DiffDepth2(lhs_only_items, lhs_only_subitems, rhs_only_items, rhs_only_subitems)

    @property
    def as_dict(self) -> dict[str, dict]:
        return {k: asdict(v) for k, v in self.items.items()}

    def members_by_name(self, key: Optional[Callable[[str], bool]] = lambda name: True) -> dict[str, set[str]]:
        return {name: set(value.members) for name, value in self.items.items() if key(name)}


def render_item_factory() -> Callable:
    def render_item(type_, obj, autogen_context) -> Union[str, bool]:
        """Callable for altering the code generated for each object.

        Use return False to leave generated code unchanged.
        """
        # autogen_context.imports.add("from fastapi_laser.alembic_ext.steps import MigrationStep")
        if isinstance(obj, sa.Column) and isinstance(obj.type, sa.Enum):
            # add operations on the entire column statement here
            return False

        if type_ == "type" and isinstance(obj, sa.Enum):
            autogen_context.imports.add("from fastapi_laser.alembic_ext.steps import enum_as_non_creatable_variant")

            return f"enum_as_non_creatable_variant(*{format_enum_args_variable_name(obj)})"

        return False

    return render_item


def get_member_removal_rules(
    enum_to_columns_map: EnumToColumnsMap, added_enum_members: Collection[str]
) -> dict[str, Optional[str]]:
    default_rules = {k: None for k in added_enum_members}
    declared_rules = enum_to_columns_map.member_removal_rules

    return default_rules | declared_rules


def get_migration_config_items(config: Config, target_metadata: MetaData) -> dict:
    target_enum_to_column_maps = EnumToColumnsMapCollection.from_metadata(metadata=target_metadata)
    online_enum_to_column_maps = EnumToColumnsMapCollection.from_metadata(metadata=get_online_metadata(config))
    enum_to_column_maps_diff = target_enum_to_column_maps.members_by_name_diff(online_enum_to_column_maps)

    migration_steps = list()
    enum_types = set()

    ############################################################
    # Add, remove or rename enum types
    ############################################################

    # added enums are only in target metadata
    enums_to_add = enum_to_column_maps_diff.lhs_only_items
    for name in enums_to_add:
        e = target_enum_to_column_maps.items[name]
        enum_types.add(e.kind)
        migration_steps.append(f"MigrationStep.for_case__create_enum(*{format_enum_args_variable_name(e.kind)})")

    # removed enums are only in the online metadata
    enums_to_remove = enum_to_column_maps_diff.rhs_only_items
    for name in enums_to_remove:
        e = online_enum_to_column_maps.items[name]
        enum_types.add(e.kind)
        migration_steps.append(f"MigrationStep.for_case__drop_enum(*{format_enum_args_variable_name(e.kind)})")

    # renamed enums are in the target metadata with the new name and in the online metadata with the old name
    # TODO: rename decorator for enum class def
    # MigrationStep.for_case__rename_enum()

    ############################################################
    # Add, remove or rename enum members
    # all enums are found in both target and online metadata
    ############################################################

    enum_members_to_add = enum_to_column_maps_diff.lhs_only_subitems
    for name, added_members in enum_members_to_add.items():
        e = target_enum_to_column_maps.items[name]
        enum_types.add(e.kind)
        step_args = ", ".join(
            (
                f"{e.columns_by_table}",
                f"{(get_member_removal_rules(e, added_members))}",
                f"*{format_enum_args_variable_name(e.kind)}",
            )
        )
        migration_steps.append(f"MigrationStep.for_case__add_enum_members({step_args})")

    enum_members_to_remove = enum_to_column_maps_diff.rhs_only_subitems
    for name, removed_members in enum_members_to_remove.items():
        e = target_enum_to_column_maps.items[name]
        enum_types.add(e.kind)
        step_args = ", ".join(
            (
                f"{e.columns_by_table}",
                f"{(get_member_removal_rules(e, removed_members))}",
                f"*{format_enum_args_variable_name(e.kind)}",
            )
        )
        migration_steps.append(f"MigrationStep.for_case__remove_enum_members({step_args})")

    # # same enum in both enum_members_to_add and enum_members_to_remove
    # TODO: rename decorator for enum class def
    # MigrationStep.for_case__rename_enum_members()

    enum_args_variable_assignments = {format_enum_args_variable_assignments(e) for e in enum_types}

    return dict(
        template_args=dict(
            enum_args_variable_assignments=enum_args_variable_assignments, migration_steps=migration_steps
        ),
        process_revision_directives=process_revision_directives_factory(
            target_enum_to_column_maps,
            online_enum_to_column_maps,
        ),
    )


def get_online_metadata(config: Config) -> MetaData:
    with get_connectable(config).connect() as connection:
        metadata = MetaData(bind=connection)
        metadata.reflect(bind=connection)
        return metadata


def get_connectable(config: Config) -> Engine:
    return engine_from_config(
        configuration=config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )


def format_enum_args_variable_assignments(enum_: Union[Type[enum.Enum], sa.Enum]) -> str:
    return f"{format_enum_args_variable_name(enum_)} = ({format_enum_args(enum_)})"


def format_enum_args_variable_name(enum_: Union[Type[enum.Enum], sa.Enum]) -> str:
    if isinstance(enum_, type(enum.Enum)):
        name = enum_.__name__.lower()
    elif isinstance(enum_, sa.Enum):
        name = enum_.name
    else:
        raise TypeError

    return f"enum_{name}_args"


def format_enum_args(enum_: Union[Type[enum.Enum], sa.Enum]) -> str:
    if isinstance(enum_, type(enum.Enum)):
        args = (enum_.__name__.lower(), *enum_._member_names_)
    elif isinstance(enum_, sa.Enum):
        args = (enum_.name, *enum_.enums)
    else:
        raise TypeError

    return ", ".join(f'"{v}"' for v in args)


# ========================================
# EXPERIMENTAL
# ========================================


class ColumnOp(NamedTuple):
    kind: str
    schema: Optional[str]
    table_name: str
    column: sa.Column


class TableOp(NamedTuple):
    kind: str
    table: sa.Table

    @property
    def columns(self) -> list[sa.Column]:
        return self.table.get_children()

    @property
    def table_name(self) -> str:
        return self.table.name


def process_revision_directives_factory(
    target_enum_to_column_maps: EnumToColumnsMapCollection, online_enum_to_column_maps: EnumToColumnsMapCollection
) -> Callable:
    def process_revision_directives(context, revision, directives) -> None:
        script = directives[0]

        upgrade_scripts_map = get_enum_names_by_op_kind(script.upgrade_ops_list)
        upgrade_add_column_enums = upgrade_scripts_map["add_column"]
        upgrade_add_table_column_enums = upgrade_scripts_map["add_table_column"]
        upgrade_remove_column_enums = upgrade_scripts_map["remove_column"]
        upgrade_remove_table_column_enums = upgrade_scripts_map["remove_table_column"]

        downgrade_scripts_map = get_enum_names_by_op_kind(script.downgrade_ops_list)
        downgrade_add_column_enums = downgrade_scripts_map["add_column"]
        downgrade_add_table_column_enums = downgrade_scripts_map["add_table_column"]
        downgrade_remove_column_enums = downgrade_scripts_map["remove_column"]
        downgrade_remove_table_column_enums = downgrade_scripts_map["remove_table_column"]

        enum_types = set()
        for name in (
            upgrade_add_column_enums
            | upgrade_add_table_column_enums
            | downgrade_remove_column_enums
            | downgrade_remove_table_column_enums
        ):
            enum_types.add(target_enum_to_column_maps.items[name].kind)

        for name in (
            upgrade_remove_column_enums
            | upgrade_remove_table_column_enums
            | downgrade_add_column_enums
            | downgrade_add_table_column_enums
        ):
            enum_types.add(online_enum_to_column_maps.items[name].kind)

        enum_args_variable_assignments = {format_enum_args_variable_assignments(e) for e in enum_types}
        context.opts["template_args"]["enum_args_variable_assignments"] = (
            context.opts["template_args"].get("enum_args_variable_assignments", []) | enum_args_variable_assignments
        )

    return process_revision_directives


def get_enum_names_by_op_kind(ops_list: Collection[OpContainer]) -> dict[str, set[str]]:
    result = dict(add_column=set(), remove_column=set(), add_table_column=set(), remove_table_column=set())
    for op in ops_list:
        for op_diff in op.as_diffs():
            try:
                column_ops = [ColumnOp(*op_diff)]
            except TypeError:
                try:
                    table_op = TableOp(*op_diff)
                    column_ops = [
                        ColumnOp(f"{table_op.kind}_column", None, table_op.table_name, column)
                        for column in table_op.columns
                    ]
                except TypeError:
                    continue

            for column_op in column_ops:
                if not isinstance(column_op.column.type, sa.Enum):
                    continue

                if column_op.kind in ("add_column", "remove_column", "add_table_column", "remove_table_column"):
                    result[column_op.kind].add(column_op.column.type.name)

    return result
