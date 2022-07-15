// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

import "deps/@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "interfaces/badger/IBadgerRegistryV2.sol";

/**
RegistryAccessControl
Written by Saj for BadgerDAO

Description:
ACL proxy for the Badger Registry V2. This contract serves two purposes:
    - Allows for the addition/removal of experimental vaults to the Registry
    from a single address. Vaults indexed to this contract's address will be displayed on the
    UI as experimental. This is to avoid having to keep track of all deployer's addresses
    and maintaining that list off-chain.
    - Allows for multiple developers (with the list controlled by the contract's admin), to
    function as the Registry's "developer" actor - can promote to experimental and demote vaults
    in a quick fashion.

NOTE: For promote() and demote() to work, this contract must be set as the "developer" on
the Badger Registry V2.

References:
BadgerRegistry repo: https://github.com/Badger-Finance/badger-registry
*/
contract RegistryAccessControl is AccessControlUpgradeable {
    // Registery Roles
    bytes32 public constant DEVELOPER_ROLE = keccak256("DEVELOPER_ROLE");

    // Addresses
    IBadgerRegistryV2 public registry;

    function initialize(address initialAdmin_, address registry_) external initializer {
        __AccessControl_init();
        _setupRole(DEFAULT_ADMIN_ROLE, initialAdmin_);
        registry = IBadgerRegistryV2(registry_);
    }

    // ===== Permissioned Functions: DEFAULT_ADMIN_ROLE =====

    /// @dev Changes the address of the Registry
    function setRegistry(address registry_) external {
        require(hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "DEFAULT_ADMIN_ROLE");
        registry = IBadgerRegistryV2(registry_);
    }

    // ===== Permissioned Functions: Developer =====

    /// @dev Add a vault to the registry under this contract's address
    /// @notice The vault will be indexed under this contract's address
    function add(
        address vault,
        string memory version,
        string memory metadata
    ) external {
        require(hasRole(DEVELOPER_ROLE, msg.sender), "DEVELOPER_ROLE");
        registry.add(vault, version, metadata);
    }

    /// @dev Remove the vault from this contract's address index
    function remove(address vault) external {
        require(hasRole(DEVELOPER_ROLE, msg.sender), "DEVELOPER_ROLE");
        registry.remove(vault);
    }

    /// @dev Promote a vault to Production on the Registry
    /// @notice Promote just means indexed by the Governance Address
    /// @notice Should this contract be set as the "developer" on the registry it will be able
    /// to promote up to experimental, otherwise this function will revert due to permissions.
    function promote(
        address vault,
        string memory version,
        string memory metadata,
        IBadgerRegistryV2.VaultStatus status
    ) external {
        require(hasRole(DEVELOPER_ROLE, msg.sender), "DEVELOPER_ROLE");
        require(registry.developer() == address(this), "Developer not set");
        registry.promote(vault, version, metadata, status);
    }

    /// @dev Demotes a vault to a lower status
    /// @notice This call will only work if this contract is set as the "developer" on the registry
    function demote(address vault, IBadgerRegistryV2.VaultStatus status) external {
        require(hasRole(DEVELOPER_ROLE, msg.sender), "DEVELOPER_ROLE");
        require(registry.developer() == address(this), "Developer not set");
        registry.demote(vault, status);
    }
}
