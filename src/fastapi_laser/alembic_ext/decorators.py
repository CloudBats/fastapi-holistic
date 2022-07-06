import enum
from typing import Optional, Type


def member_removal_db_migration_rule(**new_to_old_member_mappings: Optional[str]):
    def wrapper(cls: Type[enum.Enum]) -> Type[enum.Enum]:
        """Adds a new class attribute to track downgrade migrations.

        Adds the enum class attribute such that it does not become a member.
        If None is given as the value or the value is omitted,
        data using the value will be deleted in the migration.
        Example:
            To add "CRACKED" with a downgrade migration path to "DAMAGED", use:
            @member_removal_db_migration_rule(CRACKED="DAMAGED")
            class ObjectHealth(Enum):
                ...

        This does not account for complex cases with reoccurring values:
            1. A, B
            2. A, B, C -> @member_removal_db_migration_rule(C="A")
            3. A, B
            4. A, B, C -> @member_removal_db_migration_rule(C="B")
        In conclusion, when removing an enum member more than once,
        manually adjust the migration code.
        """
        member_removal_db_migration_rules_attr_name = "member_removal_db_migration_rules"
        cls._ignore_ = [member_removal_db_migration_rules_attr_name]
        try:
            getattr(cls, member_removal_db_migration_rules_attr_name)
        except AttributeError:
            setattr(cls, member_removal_db_migration_rules_attr_name, dict())
        cls.member_removal_db_migration_rules.update(**new_to_old_member_mappings)

        return cls

    return wrapper
