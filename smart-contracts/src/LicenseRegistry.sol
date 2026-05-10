// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {DatasetRegistry} from "./DatasetRegistry.sol";

/// @title LicenseRegistry
/// @notice On-chain license grants for datasets in `DatasetRegistry`.
///         Supports multiple license kinds with optional expiry. Only the
///         dataset owner can mint or revoke licenses.
contract LicenseRegistry {
    // -------------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------------

    enum LicenseKind {
        Personal,    // 0 — single-user, time-boxed, non-commercial
        Commercial,  // 1 — single-org commercial use, time-boxed
        Academic,    // 2 — research / non-profit
        Exclusive    // 3 — exclusive to grantee, automatically revokes others
    }

    struct License {
        uint256     id;
        uint256     datasetId;
        address     grantee;
        LicenseKind kind;
        uint64      mintedAt;
        uint64      expiresAt;   // 0 means perpetual
        bool        revoked;
        bool        exists;
    }

    // -------------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------------

    DatasetRegistry public immutable datasetRegistry;

    uint256 public nextId;
    mapping(uint256 => License)         private _licenses;
    mapping(uint256 => uint256[])       private _byDataset;   // datasetId -> license ids
    mapping(address => uint256[])       private _byGrantee;   // grantee   -> license ids

    // -------------------------------------------------------------------------
    // Events / errors
    // -------------------------------------------------------------------------

    event LicenseMinted(
        uint256 indexed id,
        uint256 indexed datasetId,
        address indexed grantee,
        LicenseKind kind,
        uint64 mintedAt,
        uint64 expiresAt
    );

    event LicenseRevoked(uint256 indexed id, uint256 indexed datasetId, uint64 at);

    error NotDatasetOwner(uint256 datasetId, address caller);
    error LicenseNotFound(uint256 id);
    error AlreadyRevoked(uint256 id);
    error InvalidGrantee();
    error InvalidExpiry();

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    constructor(address registry) {
        datasetRegistry = DatasetRegistry(registry);
    }

    // -------------------------------------------------------------------------
    // Mutating API
    // -------------------------------------------------------------------------

    /// @notice Mint a new license. Caller must be the dataset owner.
    function mintLicense(
        uint256     datasetId,
        address     grantee,
        LicenseKind kind,
        uint64      expiresAt
    )
        external
        returns (uint256 id)
    {
        // ownership check propagates `DatasetNotFound`/`NotOwner` via revert
        if (datasetRegistry.ownerOf(datasetId) != msg.sender)
            revert NotDatasetOwner(datasetId, msg.sender);
        if (grantee == address(0)) revert InvalidGrantee();
        if (expiresAt != 0 && expiresAt <= block.timestamp) revert InvalidExpiry();

        unchecked { id = ++nextId; }
        uint64 ts = uint64(block.timestamp);

        _licenses[id] = License({
            id:        id,
            datasetId: datasetId,
            grantee:   grantee,
            kind:      kind,
            mintedAt:  ts,
            expiresAt: expiresAt,
            revoked:   false,
            exists:    true
        });

        _byDataset[datasetId].push(id);
        _byGrantee[grantee].push(id);

        emit LicenseMinted(id, datasetId, grantee, kind, ts, expiresAt);
    }

    /// @notice Revoke a license (dataset owner only).
    function revoke(uint256 id) external {
        License storage lic = _licenses[id];
        if (!lic.exists) revert LicenseNotFound(id);
        if (lic.revoked) revert AlreadyRevoked(id);
        if (datasetRegistry.ownerOf(lic.datasetId) != msg.sender)
            revert NotDatasetOwner(lic.datasetId, msg.sender);

        lic.revoked = true;
        emit LicenseRevoked(id, lic.datasetId, uint64(block.timestamp));
    }

    // -------------------------------------------------------------------------
    // Read API
    // -------------------------------------------------------------------------

    function getLicense(uint256 id) external view returns (License memory) {
        License memory lic = _licenses[id];
        if (!lic.exists) revert LicenseNotFound(id);
        return lic;
    }

    function hasValidLicense(uint256 datasetId, address grantee)
        external
        view
        returns (bool)
    {
        uint256[] memory ids = _byGrantee[grantee];
        for (uint256 i = 0; i < ids.length; i++) {
            License memory lic = _licenses[ids[i]];
            if (lic.datasetId != datasetId) continue;
            if (lic.revoked) continue;
            if (lic.expiresAt != 0 && lic.expiresAt <= block.timestamp) continue;
            return true;
        }
        return false;
    }

    function licensesByDataset(uint256 datasetId) external view returns (uint256[] memory) {
        return _byDataset[datasetId];
    }

    function licensesByGrantee(address grantee) external view returns (uint256[] memory) {
        return _byGrantee[grantee];
    }
}
