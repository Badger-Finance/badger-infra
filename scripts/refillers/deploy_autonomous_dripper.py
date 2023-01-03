from calendar import timegm
from datetime import date, timedelta

from brownie import AutonomousDripper, accounts, chain, network

from helpers.addresses import r


def main(deployer_label=None):
    deployer = accounts[0] if not deployer_label else accounts.load(deployer_label)
    on_live_network = not "-fork" in network.show_active()
    if chain.id == 1:
        return AutonomousDripper.deploy(
            r.badger_wallets.techops_multisig,  # address initialOwner
            r.sett_vaults.remBADGER,  # address beneficiaryAddress
            timegm(date(2023, 1, 1).timetuple()),  # uint64 startTimestamp
            int(timedelta(days=365).total_seconds()),  # uint64 durationSeconds
            60 * 60 * 24 * 7,  # uint intervalSeconds
            [r.treasury_tokens.BADGER],  # address[] memory watchlistAddresses
            r.chainlink.keeper_registry,  # address keeperRegistryAddress
            {"from": deployer},
            publish_source=on_live_network,
        )
    # TODO: rinkeby no longer supported, use goerli instead
    # elif chain.id == 4:
    #     return AutonomousDripper.deploy(
    #         deployer,
    #         registry.rinkeby.badger_wallets.solo_multisig,
    #         timegm(date.today().timetuple()),
    #         int(timedelta(weeks=1).total_seconds()),
    #         60 * 60,  # interval of one hour
    #         [
    #             registry.rinkeby.treasury_tokens.DAI,
    #             registry.rinkeby.treasury_tokens.WBTC,
    #         ],
    #         registry.rinkeby.chainlink.keeper_registry,
    #         {"from": deployer},
    #         publish_source=on_live_network,
    #     )
