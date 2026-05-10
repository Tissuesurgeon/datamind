// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {DatasetRegistry} from "../src/DatasetRegistry.sol";
import {LicenseRegistry} from "../src/LicenseRegistry.sol";

contract LicenseRegistryTest is Test {
    DatasetRegistry internal datasets;
    LicenseRegistry internal licenses;

    address internal alice = address(0xA11CE);
    address internal bob   = address(0xB0B);
    address internal carol = address(0xCAFE);

    uint256 internal datasetId;

    function setUp() public {
        datasets = new DatasetRegistry();
        licenses = new LicenseRegistry(address(datasets));

        vm.prank(alice);
        datasetId = datasets.register(keccak256("root-1"), "0g://meta/1");
    }

    // -------------------------------------------------------------------------
    // mintLicense
    // -------------------------------------------------------------------------

    function test_mintLicense_byOwner_succeeds() public {
        vm.prank(alice);
        uint256 id = licenses.mintLicense(
            datasetId,
            bob,
            LicenseRegistry.LicenseKind.Commercial,
            uint64(block.timestamp + 30 days)
        );
        LicenseRegistry.License memory lic = licenses.getLicense(id);
        assertEq(lic.grantee, bob);
        assertEq(uint8(lic.kind), uint8(LicenseRegistry.LicenseKind.Commercial));
        assertFalse(lic.revoked);
    }

    function test_mintLicense_byNonOwner_reverts() public {
        vm.prank(bob);
        vm.expectRevert(
            abi.encodeWithSelector(LicenseRegistry.NotDatasetOwner.selector, datasetId, bob)
        );
        licenses.mintLicense(datasetId, carol, LicenseRegistry.LicenseKind.Personal, 0);
    }

    function test_mintLicense_zeroGrantee_reverts() public {
        vm.prank(alice);
        vm.expectRevert(LicenseRegistry.InvalidGrantee.selector);
        licenses.mintLicense(datasetId, address(0), LicenseRegistry.LicenseKind.Personal, 0);
    }

    function test_mintLicense_pastExpiry_reverts() public {
        vm.warp(1_000_000);
        vm.prank(alice);
        vm.expectRevert(LicenseRegistry.InvalidExpiry.selector);
        licenses.mintLicense(
            datasetId,
            bob,
            LicenseRegistry.LicenseKind.Personal,
            uint64(block.timestamp - 1)
        );
    }

    // -------------------------------------------------------------------------
    // hasValidLicense
    // -------------------------------------------------------------------------

    function test_hasValidLicense_true_whenActive() public {
        vm.prank(alice);
        licenses.mintLicense(datasetId, bob, LicenseRegistry.LicenseKind.Personal, 0);
        assertTrue(licenses.hasValidLicense(datasetId, bob));
    }

    function test_hasValidLicense_false_whenExpired() public {
        vm.warp(100);
        vm.prank(alice);
        licenses.mintLicense(
            datasetId,
            bob,
            LicenseRegistry.LicenseKind.Personal,
            uint64(block.timestamp + 50)
        );
        vm.warp(200);
        assertFalse(licenses.hasValidLicense(datasetId, bob));
    }

    function test_hasValidLicense_false_whenRevoked() public {
        vm.prank(alice);
        uint256 id = licenses.mintLicense(datasetId, bob, LicenseRegistry.LicenseKind.Personal, 0);
        vm.prank(alice);
        licenses.revoke(id);
        assertFalse(licenses.hasValidLicense(datasetId, bob));
    }

    // -------------------------------------------------------------------------
    // revoke
    // -------------------------------------------------------------------------

    function test_revoke_byNonOwner_reverts() public {
        vm.prank(alice);
        uint256 id = licenses.mintLicense(datasetId, bob, LicenseRegistry.LicenseKind.Personal, 0);
        vm.prank(bob);
        vm.expectRevert(
            abi.encodeWithSelector(LicenseRegistry.NotDatasetOwner.selector, datasetId, bob)
        );
        licenses.revoke(id);
    }

    function test_revoke_alreadyRevoked_reverts() public {
        vm.prank(alice);
        uint256 id = licenses.mintLicense(datasetId, bob, LicenseRegistry.LicenseKind.Personal, 0);
        vm.startPrank(alice);
        licenses.revoke(id);
        vm.expectRevert(abi.encodeWithSelector(LicenseRegistry.AlreadyRevoked.selector, id));
        licenses.revoke(id);
        vm.stopPrank();
    }

    // -------------------------------------------------------------------------
    // listings
    // -------------------------------------------------------------------------

    function test_licensesByDataset_lists() public {
        vm.startPrank(alice);
        licenses.mintLicense(datasetId, bob,   LicenseRegistry.LicenseKind.Personal,   0);
        licenses.mintLicense(datasetId, carol, LicenseRegistry.LicenseKind.Commercial, 0);
        vm.stopPrank();
        assertEq(licenses.licensesByDataset(datasetId).length, 2);
    }
}
