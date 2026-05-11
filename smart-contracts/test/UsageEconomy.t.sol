// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import {UsageEconomy} from "../src/UsageEconomy.sol";

contract UsageEconomyTest is Test {
    UsageEconomy internal economy;

    address internal alice    = address(0xA11CE);
    address payable internal treasury = payable(address(0xBEEF));

    function setUp() public {
        economy = new UsageEconomy(treasury, 0.01 ether, 0.05 ether, 0.001 ether);
    }

    function test_payForAction_forwardsToTreasury() public {
        vm.deal(alice, 1 ether);
        uint256 startBal = treasury.balance;

        vm.prank(alice);
        uint256 receiptId = economy.payForAction{value: 0.01 ether}(
            UsageEconomy.ActionKind.PublishDataset,
            bytes32(uint256(123))
        );

        assertEq(receiptId, 1);
        assertEq(treasury.balance - startBal, 0.01 ether);
        UsageEconomy.Receipt memory r = economy.getReceipt(receiptId);
        assertEq(r.payer, alice);
        assertEq(r.amount, 0.01 ether);
        assertEq(uint256(r.action), uint256(UsageEconomy.ActionKind.PublishDataset));
    }

    function test_payForAction_revertsOnWrongAmount() public {
        vm.deal(alice, 1 ether);
        vm.prank(alice);
        vm.expectRevert(
            abi.encodeWithSelector(
                UsageEconomy.IncorrectAmount.selector,
                0.05 ether,
                0.01 ether
            )
        );
        economy.payForAction{value: 0.01 ether}(
            UsageEconomy.ActionKind.StartTraining,
            bytes32(0)
        );
    }

    function test_freeTier_recordsReceiptWithoutTransfer() public {
        economy.setFee(UsageEconomy.ActionKind.PremiumOp, 0);
        vm.prank(alice);
        uint256 id = economy.payForAction(UsageEconomy.ActionKind.PremiumOp, bytes32(0));
        UsageEconomy.Receipt memory r = economy.getReceipt(id);
        assertEq(r.amount, 0);
    }

    function test_setFee_onlyOwner() public {
        vm.prank(alice);
        vm.expectRevert(abi.encodeWithSelector(UsageEconomy.NotOwner.selector, alice));
        economy.setFee(UsageEconomy.ActionKind.PublishDataset, 1);
    }
}
