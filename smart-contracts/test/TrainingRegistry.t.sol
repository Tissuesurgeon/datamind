// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {DatasetRegistry}  from "../src/DatasetRegistry.sol";
import {TrainingRegistry} from "../src/TrainingRegistry.sol";

contract TrainingRegistryTest is Test {
    DatasetRegistry  internal registry;
    TrainingRegistry internal training;

    address internal alice = address(0xA11CE);

    function setUp() public {
        registry = new DatasetRegistry();
        training = new TrainingRegistry(address(registry));
    }

    function _seedDataset() internal returns (uint256 datasetId) {
        vm.prank(alice);
        datasetId = registry.register(keccak256("r1"), "0g://m1");
    }

    function test_create_andTransitions() public {
        uint256 datasetId = _seedDataset();
        vm.prank(alice);
        uint256 jobId = training.createTrainingJob(datasetId, "TinyLlama-1.1B", "0g://cfg/1");
        assertEq(jobId, 1);

        TrainingRegistry.Job memory j = training.getJob(jobId);
        assertEq(j.datasetId, datasetId);
        assertEq(uint256(j.status), uint256(TrainingRegistry.Status.Pending));

        vm.prank(alice);
        training.updateTrainingStatus(jobId, TrainingRegistry.Status.Running);
        assertEq(uint256(training.getJob(jobId).status), uint256(TrainingRegistry.Status.Running));

        bytes32 ckpt = keccak256("ckpt");
        vm.prank(alice);
        training.completeTrainingJob(jobId, TrainingRegistry.Status.Succeeded, ckpt);
        TrainingRegistry.Job memory done = training.getJob(jobId);
        assertEq(uint256(done.status), uint256(TrainingRegistry.Status.Succeeded));
        assertEq(done.checkpointRoot, ckpt);
    }

    function test_create_revertsForUnknownDataset() public {
        vm.prank(alice);
        vm.expectRevert(abi.encodeWithSelector(TrainingRegistry.DatasetNotFound.selector, 99));
        training.createTrainingJob(99, "m", "c");
    }

    function test_complete_revertsAfterCompletion() public {
        uint256 datasetId = _seedDataset();
        vm.prank(alice);
        uint256 jobId = training.createTrainingJob(datasetId, "m", "c");
        vm.prank(alice);
        training.completeTrainingJob(jobId, TrainingRegistry.Status.Succeeded, bytes32(uint256(1)));

        vm.prank(alice);
        vm.expectRevert(
            abi.encodeWithSelector(
                TrainingRegistry.InvalidTransition.selector,
                TrainingRegistry.Status.Succeeded,
                TrainingRegistry.Status.Failed
            )
        );
        training.completeTrainingJob(jobId, TrainingRegistry.Status.Failed, bytes32(uint256(2)));
    }

    function test_listings() public {
        uint256 datasetId = _seedDataset();
        vm.startPrank(alice);
        training.createTrainingJob(datasetId, "m1", "c1");
        training.createTrainingJob(datasetId, "m2", "c2");
        vm.stopPrank();

        uint256[] memory byOp  = training.jobsOfOperator(alice);
        uint256[] memory byDs  = training.jobsOfDataset(datasetId);
        assertEq(byOp.length, 2);
        assertEq(byDs.length, 2);
    }
}
