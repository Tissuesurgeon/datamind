// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {DatasetRegistry} from "./DatasetRegistry.sol";

/// @title DatasetNFT
/// @notice Minimal ERC721 mint receipt for an entry in `DatasetRegistry`. One NFT
///         per registered dataset; `tokenId` mirrors the registry id so the two
///         ledgers stay in lockstep. The NFT is purely a wrapper around an
///         existing dataset record — it does not duplicate provenance storage.
/// @dev    Hand-rolled minimal ERC721 (no OpenZeppelin dependency to keep the
///         Foundry workspace self-contained).
contract DatasetNFT {
    // -------------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------------

    string public constant name   = "DataMind Dataset";
    string public constant symbol = "DMD";

    DatasetRegistry public immutable datasetRegistry;

    // tokenId => owner
    mapping(uint256 => address) private _owners;
    // owner   => balance
    mapping(address => uint256) private _balances;
    // tokenId => approved
    mapping(uint256 => address) private _tokenApprovals;
    // owner   => operator => approved
    mapping(address => mapping(address => bool)) private _operatorApprovals;
    // tokenId => metadata URI snapshot at mint time
    mapping(uint256 => string)  private _tokenURIs;
    // datasetId => minted flag (idempotency)
    mapping(uint256 => bool)    public minted;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    /// ERC721 standard events.
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    /// DataMind-specific provenance event.
    event DatasetMinted(
        uint256 indexed tokenId,
        uint256 indexed datasetId,
        address indexed owner,
        bytes32 storageRoot,
        string  tokenURI,
        uint64  mintedAt
    );

    // -------------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------------

    error DatasetNotFound(uint256 datasetId);
    error NotDatasetOwner(uint256 datasetId, address caller);
    error AlreadyMinted(uint256 datasetId);
    error TokenNotFound(uint256 tokenId);
    error NotAuthorized();
    error InvalidRecipient();

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    constructor(address registry) {
        if (registry == address(0)) revert InvalidRecipient();
        datasetRegistry = DatasetRegistry(registry);
    }

    // -------------------------------------------------------------------------
    // Mint
    // -------------------------------------------------------------------------

    /// @notice Mint a Dataset Ownership NFT for `datasetId`. Caller must be the
    ///         current dataset owner in `DatasetRegistry`. `tokenId == datasetId`.
    function mintDatasetNFT(uint256 datasetId, string calldata uri)
        external
        returns (uint256 tokenId)
    {
        DatasetRegistry.Dataset memory d = datasetRegistry.getDataset(datasetId);
        if (!d.exists) revert DatasetNotFound(datasetId);
        if (d.owner != msg.sender) revert NotDatasetOwner(datasetId, msg.sender);
        if (minted[datasetId]) revert AlreadyMinted(datasetId);

        tokenId = datasetId;
        minted[datasetId] = true;
        _owners[tokenId]   = msg.sender;
        _balances[msg.sender] += 1;
        _tokenURIs[tokenId] = uri;

        emit Transfer(address(0), msg.sender, tokenId);
        emit DatasetMinted(
            tokenId,
            datasetId,
            msg.sender,
            d.storageRoot,
            uri,
            uint64(block.timestamp)
        );
    }

    // -------------------------------------------------------------------------
    // ERC721 read API
    // -------------------------------------------------------------------------

    function balanceOf(address owner) external view returns (uint256) {
        if (owner == address(0)) revert InvalidRecipient();
        return _balances[owner];
    }

    function ownerOf(uint256 tokenId) public view returns (address) {
        address o = _owners[tokenId];
        if (o == address(0)) revert TokenNotFound(tokenId);
        return o;
    }

    function tokenURI(uint256 tokenId) external view returns (string memory) {
        if (_owners[tokenId] == address(0)) revert TokenNotFound(tokenId);
        return _tokenURIs[tokenId];
    }

    function getApproved(uint256 tokenId) external view returns (address) {
        if (_owners[tokenId] == address(0)) revert TokenNotFound(tokenId);
        return _tokenApprovals[tokenId];
    }

    function isApprovedForAll(address owner, address operator) external view returns (bool) {
        return _operatorApprovals[owner][operator];
    }

    /// @notice ERC165 minimal: ERC721 + ERC721Metadata + ERC165 itself.
    function supportsInterface(bytes4 id) external pure returns (bool) {
        return
            id == 0x80ac58cd || // ERC721
            id == 0x5b5e139f || // ERC721Metadata
            id == 0x01ffc9a7;   // ERC165
    }

    // -------------------------------------------------------------------------
    // ERC721 write API
    // -------------------------------------------------------------------------

    function approve(address to, uint256 tokenId) external {
        address owner = ownerOf(tokenId);
        if (owner != msg.sender && !_operatorApprovals[owner][msg.sender]) revert NotAuthorized();
        _tokenApprovals[tokenId] = to;
        emit Approval(owner, to, tokenId);
    }

    function setApprovalForAll(address operator, bool approved) external {
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }

    function transferFrom(address from, address to, uint256 tokenId) public {
        _transfer(from, to, tokenId);
    }

    function safeTransferFrom(address from, address to, uint256 tokenId) external {
        _transfer(from, to, tokenId);
        // We don't perform onERC721Received hook for the minimal demo; receiving
        // contracts should opt-in via standard ERC721 implementations off-chain.
    }

    function safeTransferFrom(
        address from,
        address to,
        uint256 tokenId,
        bytes calldata /* data */
    ) external {
        _transfer(from, to, tokenId);
    }

    // -------------------------------------------------------------------------
    // Internal
    // -------------------------------------------------------------------------

    function _transfer(address from, address to, uint256 tokenId) internal {
        if (to == address(0)) revert InvalidRecipient();
        address owner = ownerOf(tokenId);
        if (owner != from) revert NotAuthorized();
        if (
            msg.sender != owner &&
            _tokenApprovals[tokenId] != msg.sender &&
            !_operatorApprovals[owner][msg.sender]
        ) revert NotAuthorized();

        delete _tokenApprovals[tokenId];
        _balances[from] -= 1;
        _balances[to]   += 1;
        _owners[tokenId] = to;

        emit Transfer(from, to, tokenId);
    }
}
