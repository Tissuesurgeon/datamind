// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {DatasetRegistry} from "../src/DatasetRegistry.sol";

contract DatasetRegistryTest is Test {
    DatasetRegistry internal registry;

    address internal alice = address(0xA11CE);
    address internal bob   = address(0xB0B);

    function setUp() public {
        registry = new DatasetRegistry();
    }

    function _root(uint256 seed) internal pure returns (bytes32) {
        return keccak256(abi.encode("root", seed));
    }

    // -------------------------------------------------------------------------
    // register
    // -------------------------------------------------------------------------

    function test_register_succeeds() public {
        vm.prank(alice);
        uint256 id = registry.register(_root(1), "0g://meta/1");
        assertEq(id, 1);
        assertEq(registry.totalDatasets(), 1);
        DatasetRegistry.Dataset memory d = registry.getDataset(id);
        assertEq(d.owner, alice);
        assertEq(d.metadataURI, "0g://meta/1");
        assertEq(d.storageRoot, _root(1));
        assertTrue(d.exists);
    }

    function test_register_revertsOnEmptyRoot() public {
        vm.prank(alice);
        vm.expectRevert(DatasetRegistry.EmptyStorageRoot.selector);
        registry.register(bytes32(0), "0g://meta/1");
    }

    function test_register_revertsOnEmptyMetadataURI() public {
        vm.prank(alice);
        vm.expectRevert(DatasetRegistry.EmptyMetadataURI.selector);
        registry.register(_root(1), "");
    }

    function test_register_revertsOnDuplicateRoot() public {
        vm.prank(alice);
        registry.register(_root(1), "0g://meta/1");

        vm.prank(bob);
        vm.expectRevert(
            abi.encodeWithSelector(DatasetRegistry.DatasetAlreadyRegistered.selector, _root(1))
        );
        registry.register(_root(1), "0g://meta/2");
    }

    function test_register_emitsEvent() public {
        vm.prank(alice);
        vm.expectEmit(true, true, true, true);
        emit DatasetRegistry.DatasetRegistered(
            1,
            alice,
            _root(42),
            "0g://meta/42",
            uint64(block.timestamp)
        );
        registry.register(_root(42), "0g://meta/42");
    }

    // -------------------------------------------------------------------------
    // updateMetadata
    // -------------------------------------------------------------------------

    function test_updateMetadata_byOwner() public {
        vm.prank(alice);
        uint256 id = registry.register(_root(1), "0g://meta/1");
        vm.prank(alice);
        registry.updateMetadata(id, "0g://meta/v2");
        assertEq(registry.getDataset(id).metadataURI, "0g://meta/v2");
    }

    function test_updateMetadata_revertsForNonOwner() public {
        vm.prank(alice);
        uint256 id = registry.register(_root(1), "0g://meta/1");
        vm.prank(bob);
        vm.expectRevert(
            abi.encodeWithSelector(DatasetRegistry.NotOwner.selector, id, bob)
        );
        registry.updateMetadata(id, "0g://meta/v2");
    }

    function test_updateMetadata_revertsForUnknownId() public {
        vm.prank(alice);
        vm.expectRevert(
            abi.encodeWithSelector(DatasetRegistry.DatasetNotFound.selector, 99)
        );
        registry.updateMetadata(99, "0g://x");
    }

    // -------------------------------------------------------------------------
    // transferOwnership
    // -------------------------------------------------------------------------

    function test_transferOwnership_works() public {
        vm.prank(alice);
        uint256 id = registry.register(_root(1), "0g://meta/1");
        vm.prank(alice);
        registry.transferOwnership(id, bob);
        assertEq(registry.ownerOf(id), bob);
    }

    function test_transferOwnership_revertsForNonOwner() public {
        vm.prank(alice);
        uint256 id = registry.register(_root(1), "0g://meta/1");
        vm.prank(bob);
        vm.expectRevert(
            abi.encodeWithSelector(DatasetRegistry.NotOwner.selector, id, bob)
        );
        registry.transferOwnership(id, bob);
    }

    function test_transferOwnership_revertsOnZeroAddress() public {
        vm.prank(alice);
        uint256 id = registry.register(_root(1), "0g://meta/1");
        vm.prank(alice);
        vm.expectRevert(DatasetRegistry.InvalidRecipient.selector);
        registry.transferOwnership(id, address(0));
    }

    // -------------------------------------------------------------------------
    // listings
    // -------------------------------------------------------------------------

    function test_datasetsOf_lists() public {
        vm.startPrank(alice);
        registry.register(_root(1), "m1");
        registry.register(_root(2), "m2");
        registry.register(_root(3), "m3");
        vm.stopPrank();

        uint256[] memory ids = registry.datasetsOf(alice);
        assertEq(ids.length, 3);
        assertEq(ids[0], 1);
        assertEq(ids[2], 3);
    }
}
