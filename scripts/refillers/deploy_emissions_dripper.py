from  calendar import timegm
from datetime import date, timedelta

from brownie import EmissionsDripper, accounts, chain, network

from helpers.addresses import registry


def main(deployer_label=None):
    deployer = accounts[0] if not deployer_label else accounts.load(deployer_label)
    on_live_network = not '-fork' in network.show_active()
    if chain.id == 1:
        return EmissionsDripper.deploy(
            registry.eth.sett_vaults.remBADGER,
            timegm(date(2022, 4, 29).timetuple()),
            int(timedelta(weeks=99).total_seconds()),
            registry.eth.badger_wallets.techops_multisig,
            registry.eth.badger_wallets.dev_multisig,
            deployer,
            {'from': deployer},
            publish_source=on_live_network
        )
    elif chain.id == 4:
        return EmissionsDripper.deploy(
            registry.rinkeby.badger_wallets.solo_multisig,
            timegm(date(2022, 4, 15).timetuple()),
            int(timedelta(weeks=11).total_seconds()),
            registry.rinkeby.badger_wallets.rinkeby_multisig,
            registry.rinkeby.badger_wallets.rinkeby_multisig,
            deployer,
            {'from': deployer},
            publish_source=on_live_network
        )
