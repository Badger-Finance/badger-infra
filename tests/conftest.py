import pytest
from brownie import accounts

from helpers.addresses import registry


@pytest.fixture
def dev():
    return accounts.at(registry.eth.badger_wallets.dev_multisig, force=True)


@pytest.fixture
def techops():
    return accounts.at(registry.eth.badger_wallets.techops_multisig, force=True)
