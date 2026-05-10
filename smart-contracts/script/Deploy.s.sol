// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import {DatasetRegistry} from "../src/DatasetRegistry.sol";
import {LicenseRegistry} from "../src/LicenseRegistry.sol";

/// @notice Deploys DatasetRegistry + LicenseRegistry to the configured RPC.
/// @dev    Defaults are tuned for the 0G Galileo testnet (chain id 16602).
///
///         Usage:
///           forge script script/Deploy.s.sol:Deploy \
///             --rpc-url $OG_EVM_RPC \
///             --private-key $OG_PRIVATE_KEY \
///             --broadcast
contract Deploy is Script {
    function run() external returns (DatasetRegistry registry, LicenseRegistry licenses) {
        uint256 pk = vm.envOr("OG_PRIVATE_KEY", uint256(0));
        if (pk == 0) {
            // Local foundry default; fine for `forge script` simulations.
            pk = vm.envOr("PRIVATE_KEY", uint256(0));
        }
        require(pk != 0, "Set OG_PRIVATE_KEY (or PRIVATE_KEY) before deploying.");

        vm.startBroadcast(pk);

        registry = new DatasetRegistry();
        licenses = new LicenseRegistry(address(registry));

        vm.stopBroadcast();

        console2.log("DatasetRegistry deployed at:", address(registry));
        console2.log("LicenseRegistry deployed at:", address(licenses));
    }
}
