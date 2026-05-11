// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title UsageEconomy
/// @notice Lightweight fee router for DataMind actions paid in the native 0G
///         testnet token. Users call `payForAction` (or one of the typed
///         wrappers) and the platform records a receipt + forwards funds to
///         the configured treasury. No staking, no governance — just a
///         hackathon-friendly, transparent fee ledger.
contract UsageEconomy {
    // -------------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------------

    enum ActionKind {
        PublishDataset,  // 0
        StartTraining,   // 1
        PremiumOp        // 2
    }

    struct Receipt {
        uint256 id;
        address payer;
        ActionKind action;
        bytes32 ref;     // free-form reference (datasetId, jobId, etc.)
        uint256 amount;
        uint64  paidAt;
    }

    // -------------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------------

    address public owner;
    address payable public treasury;
    mapping(ActionKind => uint256) public feeFor;

    uint256 public nextReceiptId;
    mapping(uint256 => Receipt) private _receipts;
    mapping(address => uint256[]) private _byPayer;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    event ActionPaid(
        uint256 indexed receiptId,
        address indexed payer,
        ActionKind indexed action,
        bytes32 ref,
        uint256 amount,
        uint64  paidAt
    );

    event FeeUpdated(ActionKind indexed action, uint256 newFee);
    event TreasuryUpdated(address indexed newTreasury);
    event OwnerTransferred(address indexed previousOwner, address indexed newOwner);

    // -------------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------------

    error NotOwner(address caller);
    error InvalidTreasury();
    error IncorrectAmount(uint256 expected, uint256 received);
    error TransferFailed();

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    /// @param _treasury     Address that receives fees.
    /// @param _publishFee   Wei charged to publish a dataset.
    /// @param _trainingFee  Wei charged to start a training job.
    /// @param _premiumFee   Wei charged for premium AI operations.
    constructor(
        address payable _treasury,
        uint256 _publishFee,
        uint256 _trainingFee,
        uint256 _premiumFee
    ) {
        if (_treasury == address(0)) revert InvalidTreasury();
        owner    = msg.sender;
        treasury = _treasury;
        feeFor[ActionKind.PublishDataset] = _publishFee;
        feeFor[ActionKind.StartTraining]  = _trainingFee;
        feeFor[ActionKind.PremiumOp]      = _premiumFee;
    }

    // -------------------------------------------------------------------------
    // Pay
    // -------------------------------------------------------------------------

    /// @notice Pay for a DataMind action. `msg.value` must equal `feeFor[kind]`.
    ///         If the fee is zero, this still records a free-tier receipt.
    /// @param kind   Action type.
    /// @param ref    Off-chain reference (e.g. bytes32 of dataset id).
    function payForAction(ActionKind kind, bytes32 ref) external payable returns (uint256 receiptId) {
        uint256 expected = feeFor[kind];
        if (msg.value != expected) revert IncorrectAmount(expected, msg.value);

        unchecked { receiptId = ++nextReceiptId; }
        uint64 ts = uint64(block.timestamp);

        _receipts[receiptId] = Receipt({
            id:     receiptId,
            payer:  msg.sender,
            action: kind,
            ref:    ref,
            amount: msg.value,
            paidAt: ts
        });
        _byPayer[msg.sender].push(receiptId);

        if (msg.value > 0) {
            (bool ok, ) = treasury.call{value: msg.value}("");
            if (!ok) revert TransferFailed();
        }

        emit ActionPaid(receiptId, msg.sender, kind, ref, msg.value, ts);
    }

    // -------------------------------------------------------------------------
    // Read API
    // -------------------------------------------------------------------------

    function getReceipt(uint256 id) external view returns (Receipt memory) {
        return _receipts[id];
    }

    function receiptsOf(address payer) external view returns (uint256[] memory) {
        return _byPayer[payer];
    }

    // -------------------------------------------------------------------------
    // Admin
    // -------------------------------------------------------------------------

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner(msg.sender);
        _;
    }

    function setFee(ActionKind kind, uint256 newFee) external onlyOwner {
        feeFor[kind] = newFee;
        emit FeeUpdated(kind, newFee);
    }

    function setTreasury(address payable newTreasury) external onlyOwner {
        if (newTreasury == address(0)) revert InvalidTreasury();
        treasury = newTreasury;
        emit TreasuryUpdated(newTreasury);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert InvalidTreasury();
        address prev = owner;
        owner = newOwner;
        emit OwnerTransferred(prev, newOwner);
    }
}
