from app import module_based_router_factory

from . import api_v1, jobs, migrations, probes, tests


router = module_based_router_factory(api_v1, probes, tests, jobs, migrations)
