from app import module_based_router_factory

# import modules in the current directory and use them directly in the router
from . import items


router = module_based_router_factory(items)
