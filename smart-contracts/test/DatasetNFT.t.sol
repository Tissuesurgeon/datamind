// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {DatasetRegistry} from "../src/DatasetRegistry.sol";
import {DatasetNFT}      from "../src/DatasetNFT.sol";

contract DatasetNFTTest is Test {
    DatasetRegistry internal registry;
    DatasetNFT      internal nft;

    address internal alice = address(0xA11CE);
    address internal bob   = address(0xB0B);

    function setUp() public {
        registry = new DatasetRegistry();
        nft      = new DatasetNFT(address(registry));
    }

    function _registerAs(address who, uint256 seed) internal returns (uint256 id) {
        vm.prank(who);
        id = registry.register(keccak256(abi.encode("root", seed)), "0g://meta/x");
    }

    function test_mint_succeedsForOwner() public {
        uint256 id = _registerAs(alice, 1);
        vm.prank(alice);
        uint256 tokenId = nft.mintDatasetNFT(id, "0g://nft/1");
        assertEq(tokenId, id);
        assertEq(nft.ownerOf(tokenId), alice);
        assertEq(nft.tokenURI(tokenId), "0g://nft/1");
        assertTrue(nft.minted(id));
    }

    function test_mint_revertsForNonOwner() public {
        uint256 id = _registerAs(alice, 1);
        vm.prank(bob);
        vm.expectRevert(
            abi.encodeWithSelector(DatasetNFT.NotDatasetOwner.selector, id, bob)
        );
        nft.mintDatasetNFT(id, "0g://nft/1");
    }

    function test_mint_revertsForUnknownDataset() public {
        vm.prank(alice);
        vm.expectRevert(
            abi.encodeWithSelector(DatasetRegistry.DatasetNotFound.selector, 99)
        );
        nft.mintDatasetNFT(99, "x");
    }

    function test_mint_revertsOnDoubleMint() public {
        uint256 id = _registerAs(alice, 1);
        vm.prank(alice);
        nft.mintDatasetNFT(id, "u1");
        vm.prank(alice);
        vm.expectRevert(abi.encodeWithSelector(DatasetNFT.AlreadyMinted.selector, id));
        nft.mintDatasetNFT(id, "u2");
    }

    function test_transfer_movesOwnership() public {
        uint256 id = _registerAs(alice, 7);
        vm.prank(alice);
        nft.mintDatasetNFT(id, "u1");
        vm.prank(alice);
        nft.transferFrom(alice, bob, id);
        assertEq(nft.ownerOf(id), bob);
    }

    function test_supportsInterface() public view {
        assertTrue(nft.supportsInterface(0x80ac58cd));
        assertTrue(nft.supportsInterface(0x5b5e139f));
        assertTrue(nft.supportsInterface(0x01ffc9a7));
        assertFalse(nft.supportsInterface(0xffffffff));
    }
}
