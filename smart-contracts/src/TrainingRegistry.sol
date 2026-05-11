// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {DatasetRegistry} from "./DatasetRegistry.sol";

/// @title TrainingRegistry
/// @notice On-chain registry for AI training jobs. Each job references a
///         dataset id from `DatasetRegistry` and records lifecycle transitions
///         + an optional final checkpoint storage root (0G Storage merkle root).
contract TrainingRegistry {
    // -------------------------------------------------------------------------
    // Types
    // -------------------------------------------------------------------------

    enum Status {
        Pending,     // 0 — created, awaiting compute
        Running,     // 1 — training in progress
        Succeeded,   // 2 — finished, checkpoint anchored
        Failed,      // 3 — irrecoverable error
        Cancelled    // 4 — operator-cancelled
    }

    struct Job {
        uint256 id;
        uint256 datasetId;
        address operator;       // who launched / paid for the job
        string  baseModel;      // freeform e.g. "TinyLlama-1.1B"
        string  configURI;      // 0g:// pointer to training config JSON
        bytes32 checkpointRoot; // 0 until completion
        Status  status;
        uint64  createdAt;
        uint64  updatedAt;
        bool    exists;
    }

    // -------------------------------------------------------------------------
    // Storage
    // -------------------------------------------------------------------------

    DatasetRegistry public immutable datasetRegistry;

    uint256 public nextId;
    mapping(uint256 => Job)       private _jobs;
    mapping(address => uint256[]) private _byOperator;
    mapping(uint256 => uint256[]) private _byDataset;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    event TrainingStarted(
        uint256 indexed id,
        uint256 indexed datasetId,
        address indexed operator,
        string  baseModel,
        string  configURI,
        uint64  createdAt
    );

    event TrainingUpdated(
        uint256 indexed id,
        Status  status,
        uint64  at
    );

    event TrainingCompleted(
        uint256 indexed id,
        Status  status,
        bytes32 checkpointRoot,
        uint64  at
    );

    // -------------------------------------------------------------------------
    // Errors
    // -------------------------------------------------------------------------

    error DatasetNotFound(uint256 datasetId);
    error JobNotFound(uint256 id);
    error NotOperator(uint256 id, address caller);
    error InvalidTransition(Status from, Status to);
    error EmptyBaseModel();

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    constructor(address registry) {
        datasetRegistry = DatasetRegistry(registry);
    }

    // -------------------------------------------------------------------------
    // Mutating API
    // -------------------------------------------------------------------------

    /// @notice Open a new training job. Anyone can train on any dataset; the
    ///         registry only records authorship. License checks live in the
    ///         off-chain pipeline + `LicenseRegistry`.
    function createTrainingJob(
        uint256 datasetId,
        string calldata baseModel,
        string calldata configURI
    ) external returns (uint256 id) {
        if (!datasetRegistry.exists(datasetId)) revert DatasetNotFound(datasetId);
        if (bytes(baseModel).length == 0) revert EmptyBaseModel();

        unchecked { id = ++nextId; }
        uint64 ts = uint64(block.timestamp);

        _jobs[id] = Job({
            id:             id,
            datasetId:      datasetId,
            operator:       msg.sender,
            baseModel:      baseModel,
            configURI:      configURI,
            checkpointRoot: bytes32(0),
            status:         Status.Pending,
            createdAt:      ts,
            updatedAt:      ts,
            exists:         true
        });

        _byOperator[msg.sender].push(id);
        _byDataset[datasetId].push(id);

        emit TrainingStarted(id, datasetId, msg.sender, baseModel, configURI, ts);
    }

    /// @notice Update a job to `Running`. Idempotent: re-emitting `Running` is
    ///         allowed for re-attempts after transient infra failures.
    function updateTrainingStatus(uint256 id, Status to) external {
        Job storage j = _jobs[id];
        if (!j.exists) revert JobNotFound(id);
        if (j.operator != msg.sender) revert NotOperator(id, msg.sender);

        // Only `Pending → Running` or `Running → Cancelled` is allowed via
        // this entrypoint. Completion (Succeeded/Failed) goes through
        // `completeTrainingJob` so we always carry a checkpoint reference.
        bool ok =
            (j.status == Status.Pending && to == Status.Running) ||
            (j.status == Status.Running && to == Status.Cancelled) ||
            (j.status == Status.Pending && to == Status.Cancelled);
        if (!ok) revert InvalidTransition(j.status, to);

        j.status    = to;
        j.updatedAt = uint64(block.timestamp);
        emit TrainingUpdated(id, to, j.updatedAt);
    }

    /// @notice Mark the job as `Succeeded` or `Failed` and anchor the final
    ///         checkpoint storage root (0G Storage merkle root for the
    ///         checkpoint manifest).
    function completeTrainingJob(uint256 id, Status finalStatus, bytes32 checkpointRoot) external {
        Job storage j = _jobs[id];
        if (!j.exists) revert JobNotFound(id);
        if (j.operator != msg.sender) revert NotOperator(id, msg.sender);

        if (
            finalStatus != Status.Succeeded &&
            finalStatus != Status.Failed
        ) revert InvalidTransition(j.status, finalStatus);
        if (j.status == Status.Succeeded || j.status == Status.Failed || j.status == Status.Cancelled) {
            revert InvalidTransition(j.status, finalStatus);
        }

        j.status         = finalStatus;
        j.checkpointRoot = checkpointRoot;
        j.updatedAt      = uint64(block.timestamp);

        emit TrainingCompleted(id, finalStatus, checkpointRoot, j.updatedAt);
    }

    // -------------------------------------------------------------------------
    // Read API
    // -------------------------------------------------------------------------

    function getJob(uint256 id) external view returns (Job memory) {
        Job memory j = _jobs[id];
        if (!j.exists) revert JobNotFound(id);
        return j;
    }

    function jobsOfOperator(address op) external view returns (uint256[] memory) {
        return _byOperator[op];
    }

    function jobsOfDataset(uint256 datasetId) external view returns (uint256[] memory) {
        return _byDataset[datasetId];
    }

    function totalJobs() external view returns (uint256) {
        return nextId;
    }
}
