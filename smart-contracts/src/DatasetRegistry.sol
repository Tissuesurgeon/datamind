// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title DatasetRegistry
/// @notice On-chain provenance and ownership ledger for AI-ready datasets.
///         Each dataset is identified by a `bytes32 storageRoot` (the 0G Storage
///         merkle root) and carries a `metadataURI` (typically a 0G storage hash
///         pointing to a JSON document with title, description, tags, schema).
/// @dev    Designed for 0G Galileo testnet (chain id 16602) but chain-agnostic.
contract DatasetRegistry {
    // -------------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------------

    struct Dataset {
        uint256 id;
        address owner;
        bytes32 storageRoot;     // 0G Storage merkle root of the file payload
        string  metadataURI;     // pointer to JSON manifest (0G hash or URL)
        uint64  createdAt;
        uint64  updatedAt;
        bool    exists;
    }

    // -------------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------------

    uint256 public nextId;
    mapping(uint256 => Dataset)            private _datasets;
    mapping(address => uint256[])          private _ownedByAddress;
    mapping(bytes32 => uint256)            public  rootToId;   // 1-indexed; 0 = absent

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    event DatasetRegistered(
        uint256 indexed id,
        address indexed owner,
        bytes32 indexed storageRoot,
        string  metadataURI,
        uint64  createdAt
    );

    event DatasetMetadataUpdated(
        uint256 indexed id,
        string  metadataURI,
        uint64  updatedAt
    );

    event DatasetTransferred(
        uint256 indexed id,
        address indexed from,
        address indexed to,
        uint64  at
    );

    // -------------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------------

    error EmptyStorageRoot();
    error EmptyMetadataURI();
    error DatasetAlreadyRegistered(bytes32 storageRoot);
    error DatasetNotFound(uint256 id);
    error NotOwner(uint256 id, address caller);
    error InvalidRecipient();

    // -------------------------------------------------------------------------
    // Modifiers
    // -------------------------------------------------------------------------

    modifier onlyOwnerOf(uint256 id) {
        Dataset storage d = _datasets[id];
        if (!d.exists) revert DatasetNotFound(id);
        if (d.owner != msg.sender) revert NotOwner(id, msg.sender);
        _;
    }

    // -------------------------------------------------------------------------
    // Mutating API
    // -------------------------------------------------------------------------

    /// @notice Register a new dataset.
    /// @param storageRoot  0G Storage merkle root of the file payload (non-zero).
    /// @param metadataURI  Pointer to JSON manifest (0G hash or URL, non-empty).
    /// @return id          Newly allocated dataset id.
    function register(bytes32 storageRoot, string calldata metadataURI)
        external
        returns (uint256 id)
    {
        if (storageRoot == bytes32(0)) revert EmptyStorageRoot();
        if (bytes(metadataURI).length == 0) revert EmptyMetadataURI();
        if (rootToId[storageRoot] != 0) revert DatasetAlreadyRegistered(storageRoot);

        unchecked { id = ++nextId; }
        uint64 ts = uint64(block.timestamp);

        _datasets[id] = Dataset({
            id:           id,
            owner:        msg.sender,
            storageRoot:  storageRoot,
            metadataURI:  metadataURI,
            createdAt:    ts,
            updatedAt:    ts,
            exists:       true
        });

        rootToId[storageRoot] = id;
        _ownedByAddress[msg.sender].push(id);

        emit DatasetRegistered(id, msg.sender, storageRoot, metadataURI, ts);
    }

    /// @notice Update the metadata URI for a dataset (owner only).
    function updateMetadata(uint256 id, string calldata metadataURI)
        external
        onlyOwnerOf(id)
    {
        if (bytes(metadataURI).length == 0) revert EmptyMetadataURI();
        Dataset storage d = _datasets[id];
        d.metadataURI = metadataURI;
        d.updatedAt   = uint64(block.timestamp);
        emit DatasetMetadataUpdated(id, metadataURI, d.updatedAt);
    }

    /// @notice Transfer ownership of a dataset.
    function transferOwnership(uint256 id, address to)
        external
        onlyOwnerOf(id)
    {
        if (to == address(0)) revert InvalidRecipient();
        Dataset storage d = _datasets[id];
        address prev = d.owner;
        d.owner     = to;
        d.updatedAt = uint64(block.timestamp);

        _ownedByAddress[to].push(id);
        // Note: leaving the id in the previous owner's list is intentional for
        // O(1) transfer cost; off-chain consumers should filter by current
        // owner via `getDataset(id).owner`. A linear-scan removal can be added
        // later if needed.
        emit DatasetTransferred(id, prev, to, d.updatedAt);
    }

    // -------------------------------------------------------------------------
    // Read API
    // -------------------------------------------------------------------------

    function getDataset(uint256 id) external view returns (Dataset memory) {
        Dataset memory d = _datasets[id];
        if (!d.exists) revert DatasetNotFound(id);
        return d;
    }

    function exists(uint256 id) external view returns (bool) {
        return _datasets[id].exists;
    }

    function ownerOf(uint256 id) external view returns (address) {
        Dataset memory d = _datasets[id];
        if (!d.exists) revert DatasetNotFound(id);
        return d.owner;
    }

    /// @return ids list of dataset ids the address has ever owned (current
    ///         owner can be confirmed via `getDataset(id).owner == owner`).
    function datasetsOf(address owner) external view returns (uint256[] memory ids) {
        return _ownedByAddress[owner];
    }

    function totalDatasets() external view returns (uint256) {
        return nextId;
    }
}
