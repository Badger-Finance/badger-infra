from datetime import datetime
import brownie
import pytest
from brownie import accounts, interface, RegistryAccessControl, chain
from helpers.addresses import registry

### FIXTURES ###

# Avoiding real vault addresses since the registry doesn't like duplicates
VAULT = "0x1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a"
RANDOM_ADDRESS = "0xb2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2"

@pytest.fixture(scope='module')
def deployer():
    return accounts[0]

@pytest.fixture(scope='module')
def deployer2():
    return accounts[1]

@pytest.fixture(scope='module')
def registry_v2():
    return interface.IBadgerRegistryV2(registry.eth.registry_v2)

@pytest.fixture(scope='module')
def governance(registry_v2):
    return accounts.at(registry_v2.governance(), force=True)

@pytest.fixture(scope='module')
def strategistGuild(registry_v2):
    return accounts.at(registry_v2.strategistGuild(), force=True)

@pytest.fixture(scope='module')
def registry_acl(deployer, strategistGuild, registry_v2):
    contract = RegistryAccessControl.deploy({"from": deployer})
    contract.initialize(strategistGuild.address, registry_v2.address, {"from": deployer})
    return contract

@pytest.fixture(scope='module', autouse=True)
def state_setup(governance, strategistGuild, deployer, deployer2, registry_acl, registry_v2):
    # Set registryACL as "developer" on registry
    registry_v2.setDeveloper(registry_acl, {"from": governance})
    # Add the deployers as developers on the ACL
    role = registry_acl.DEVELOPER_ROLE()
    registry_acl.grantRole(role, deployer.address, {"from": strategistGuild})
    registry_acl.grantRole(role, deployer2.address, {"from": strategistGuild})

### TESTS ###

def test_add_remove(deployer, deployer2, registry_acl, registry_v2):
    # No vaults have been added by deployer nor the ACL contract
    assert registry_v2.getVaults("V1.5", registry_acl) == []
    assert registry_v2.getVaults("V1.5", deployer) == []
    assert registry_v2.getVaults("V1.5", deployer2) == []

    # We add a vault through the ACL with the first deployer
    tx = registry_acl.add(VAULT, "v1.5", "name=BTC-CVX,protocol=Badger,behavior=DCA", {"from": deployer})
    assert registry_v2.getVaults("v1.5", registry_acl) == [[VAULT, "v1.5", "1", "name=BTC-CVX,protocol=Badger,behavior=DCA"]]
    assert registry_v2.getVaults("V1.5", deployer) == []
    assert registry_v2.getVaults("V1.5", deployer2) == []

    event = tx.events["NewVault"][0]
    assert event["author"] == registry_acl.address
    assert event["vault"] == VAULT

    # We remove the vault through the ACL using a different deployer
    tx = registry_acl.remove(VAULT, {"from": deployer2})
    assert registry_v2.getVaults("V1.5", registry_acl) == []
    assert registry_v2.getVaults("V1.5", deployer) == []
    assert registry_v2.getVaults("V1.5", deployer2) == []

    event = tx.events["RemoveVault"][0]
    assert event["author"] == registry_acl.address
    assert event["vault"] == VAULT


def test_promote(deployer, registry_acl, registry_v2):
    # deployer attempts to promote to "Open" (3) but promotion is only possible to "experimental" (1)
    tx = registry_acl.promote(VAULT, "v1.5", "name=BTC-CVX,protocol=Badger,behavior=DCA", 3, {"from": deployer})
    assert [VAULT, "v1.5", "1", "name=BTC-CVX,protocol=Badger,behavior=DCA"] not in registry_v2.getFilteredProductionVaults("v1.5", 3)
    assert [VAULT, "v1.5", "1", "name=BTC-CVX,protocol=Badger,behavior=DCA"] in registry_v2.getFilteredProductionVaults("v1.5", 1)

    event = tx.events["PromoteVault"][0]
    assert event["author"] == registry_acl.address
    assert event["vault"] == VAULT
    assert event["status"] == 1


def test_demote(deployer2, strategistGuild, registry_acl, registry_v2):
    # strategistGuild promotes a vault to open (3)
    registry_v2.promote(VAULT, "v1.5", "name=BTC-CVX,protocol=Badger,behavior=DCA", 3, {"from": strategistGuild})
    assert [VAULT, "v1.5", "3", "name=BTC-CVX,protocol=Badger,behavior=DCA"] in registry_v2.getFilteredProductionVaults("v1.5", 3)

    # deployer demotes vault to deprecated (0)
    tx = registry_acl.demote(VAULT, 0, {"from": deployer2})
    assert [VAULT, "v1.5", "0", "name=BTC-CVX,protocol=Badger,behavior=DCA"] not in registry_v2.getFilteredProductionVaults("v1.5", 3)
    assert [VAULT, "v1.5", "0", "name=BTC-CVX,protocol=Badger,behavior=DCA"] in registry_v2.getFilteredProductionVaults("v1.5", 0)

    event = tx.events["DemoteVault"][0]
    assert event["author"] == registry_acl.address
    assert event["vault"] == VAULT
    assert event["status"] == 0


def test_permissions(deployer2, deployer, strategistGuild, governance, registry_acl, registry_v2):
    rando = accounts[5]
    actors = [
        deployer,
        deployer2,
        strategistGuild,
        rando
    ]

    developers = [deployer, deployer2]

    ### DEVELOPER_ROLE permissions ###

    # add()
    chain.snapshot() # Can't add the same vault twice
    for actor in actors:
        if actor in developers:
            registry_acl.add(VAULT, "v1.5", "name=BTC-CVX,protocol=Badger,behavior=DCA", {"from": actor})
            chain.revert()
        else:
            with brownie.reverts("DEVELOPER_ROLE"):
                registry_acl.add(VAULT, "v1.5", "name=BTC-CVX,protocol=Badger,behavior=DCA", {"from": actor})

    # remove()
    registry_acl.add(VAULT, "v1.5", "name=BTC-CVX,protocol=Badger,behavior=DCA", {"from": deployer}) # We add a vault
    chain.snapshot()
    for actor in actors:
        if actor in developers:
            registry_acl.remove(VAULT, {"from": actor})
            chain.revert()
        else:
            with brownie.reverts("DEVELOPER_ROLE"):
                registry_acl.remove(VAULT, {"from": actor})

    # promote()
    for actor in actors:
        if actor in developers:
            registry_acl.promote(VAULT, "v1.5", "name=BTC-CVX,protocol=Badger,behavior=DCA", 1, {"from": actor})
            chain.revert()
        else:
            with brownie.reverts("DEVELOPER_ROLE"):
                registry_acl.promote(VAULT, "v1.5", "name=BTC-CVX,protocol=Badger,behavior=DCA", 1, {"from": actor})

    # demote()
    registry_v2.promote(VAULT, "v1.5", "name=BTC-CVX,protocol=Badger,behavior=DCA", 3, {"from": strategistGuild}) # Promote a vault
    chain.snapshot()
    for actor in actors:
        if actor in developers:
            registry_acl.demote(VAULT, 0, {"from": actor})
            chain.revert()
        else:
            with brownie.reverts("DEVELOPER_ROLE"):
                registry_acl.demote(VAULT, 0, {"from": actor})


    ### DEFAULT_ADMIN_ROLE permissions ###

    # grantRole()
    for actor in actors:
        role = registry_acl.DEVELOPER_ROLE()
        if actor == strategistGuild:
            registry_acl.grantRole(role, rando.address, {"from": actor})
        else:
            with brownie.reverts("AccessControl: sender must be an admin to grant"):
                registry_acl.grantRole(role, rando.address, {"from": actor})

    # setRegistry()
    chain.snapshot()
    for actor in actors:
        if actor == strategistGuild:
            registry_acl.setRegistry(RANDOM_ADDRESS, {"from": actor})
            chain.revert()
        else:
            with brownie.reverts("DEFAULT_ADMIN_ROLE"):
                registry_acl.setRegistry(RANDOM_ADDRESS, {"from": actor})


    ### RegistryACL not set as developer on Registry ###

    registry_v2.setDeveloper(deployer, {"from": governance})

    # Promotions and demotions should fail
    with brownie.reverts("Developer not set"):
        registry_acl.demote(VAULT, 0, {"from": developers[0]})
    
    with brownie.reverts("Developer not set"):
        registry_acl.promote(VAULT, "v1.5", "name=BTC-CVX,protocol=Badger,behavior=DCA", 1, {"from": developers[0]})    