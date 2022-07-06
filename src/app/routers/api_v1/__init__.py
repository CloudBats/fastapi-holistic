from app import module_based_router_factory

from . import balances, conversions, payments, rates, reference


router = module_based_router_factory(balances, conversions, payments, rates, reference)
