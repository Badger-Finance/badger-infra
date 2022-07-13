// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

import "deps/@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "interfaces/badger/IBadgerRegistryV2.sol";

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
