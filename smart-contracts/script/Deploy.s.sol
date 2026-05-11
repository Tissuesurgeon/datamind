// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import {DatasetRegistry} from "../src/DatasetRegistry.sol";
import {DatasetNFT}      from "../src/DatasetNFT.sol";
import {TrainingRegistry} from "../src/TrainingRegistry.sol";
import {LicenseRegistry} from "../src/LicenseRegistry.sol";
import {UsageEconomy}    from "../src/UsageEconomy.sol";

/// @notice Deploys the DataMind protocol contracts to the configured RPC.
/// @dev    Defaults are tuned for the 0G Galileo testnet (chain id 16602).
///
///         Usage:
///           forge script script/Deploy.s.sol:Deploy \
///             --rpc-url $OG_EVM_RPC \
///             --private-key $OG_PRIVATE_KEY \
///             --broadcast
///
///         Optional env (with sane defaults):
///           DATAMIND_TREASURY       — fee recipient (default = deployer)
///           DATAMIND_PUBLISH_FEE    — wei (default 0)
///           DATAMIND_TRAINING_FEE   — wei (default 0)
///           DATAMIND_PREMIUM_FEE    — wei (default 0)
contract Deploy is Script {
    function run()
        external
        returns (
            DatasetRegistry  registry,
            DatasetNFT       nft,
            TrainingRegistry training,
            LicenseRegistry  licenses,
            UsageEconomy     economy
        )
    {
        uint256 pk = vm.envOr("OG_PRIVATE_KEY", uint256(0));
        if (pk == 0) {
            pk = vm.envOr("PRIVATE_KEY", uint256(0));
        }
        require(pk != 0, "Set OG_PRIVATE_KEY (or PRIVATE_KEY) before deploying.");

        address deployer = vm.addr(pk);
        address payable treasury = payable(vm.envOr("DATAMIND_TREASURY", deployer));
        uint256 publishFee  = vm.envOr("DATAMIND_PUBLISH_FEE",  uint256(0));
        uint256 trainingFee = vm.envOr("DATAMIND_TRAINING_FEE", uint256(0));
        uint256 premiumFee  = vm.envOr("DATAMIND_PREMIUM_FEE",  uint256(0));

        vm.startBroadcast(pk);

        registry = new DatasetRegistry();
        nft      = new DatasetNFT(address(registry));
        training = new TrainingRegistry(address(registry));
        licenses = new LicenseRegistry(address(registry));
        economy  = new UsageEconomy(treasury, publishFee, trainingFee, premiumFee);

        vm.stopBroadcast();

        console2.log("DatasetRegistry  :", address(registry));
        console2.log("DatasetNFT       :", address(nft));
        console2.log("TrainingRegistry :", address(training));
        console2.log("LicenseRegistry  :", address(licenses));
        console2.log("UsageEconomy     :", address(economy));
        console2.log("Treasury         :", treasury);
    }
}
