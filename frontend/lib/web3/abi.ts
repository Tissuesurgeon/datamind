/**
 * Minimal ABIs for DataMind protocol contracts. These mirror the public surface
 * defined in `smart-contracts/src/*.sol`. They are intentionally hand-written
 * (rather than imported from `smart-contracts/out`) so the frontend bundle does
 * not need to be regenerated every time Forge produces new artifacts.
 *
 * If you change a function signature in Solidity, update the matching entry
 * here. Tests are at `smart-contracts/test/*.t.sol`.
 */

export const DATASET_REGISTRY_ABI = [
  {
    type: "function",
    name: "register",
    stateMutability: "nonpayable",
    inputs: [
      { name: "storageRoot", type: "bytes32" },
      { name: "metadataURI", type: "string" },
    ],
    outputs: [{ name: "id", type: "uint256" }],
  },
  {
    type: "function",
    name: "updateMetadata",
    stateMutability: "nonpayable",
    inputs: [
      { name: "id", type: "uint256" },
      { name: "metadataURI", type: "string" },
    ],
    outputs: [],
  },
  {
    type: "function",
    name: "getDataset",
    stateMutability: "view",
    inputs: [{ name: "id", type: "uint256" }],
    outputs: [
      {
        name: "",
        type: "tuple",
        components: [
          { name: "id", type: "uint256" },
          { name: "owner", type: "address" },
          { name: "storageRoot", type: "bytes32" },
          { name: "metadataURI", type: "string" },
          { name: "createdAt", type: "uint64" },
          { name: "updatedAt", type: "uint64" },
          { name: "exists", type: "bool" },
        ],
      },
    ],
  },
  {
    type: "function",
    name: "ownerOf",
    stateMutability: "view",
    inputs: [{ name: "id", type: "uint256" }],
    outputs: [{ name: "", type: "address" }],
  },
  {
    type: "function",
    name: "exists",
    stateMutability: "view",
    inputs: [{ name: "id", type: "uint256" }],
    outputs: [{ name: "", type: "bool" }],
  },
  {
    type: "function",
    name: "rootToId",
    stateMutability: "view",
    inputs: [{ name: "", type: "bytes32" }],
    outputs: [{ name: "", type: "uint256" }],
  },
  {
    type: "event",
    name: "DatasetRegistered",
    inputs: [
      { name: "id", type: "uint256", indexed: true },
      { name: "owner", type: "address", indexed: true },
      { name: "storageRoot", type: "bytes32", indexed: true },
      { name: "metadataURI", type: "string", indexed: false },
      { name: "createdAt", type: "uint64", indexed: false },
    ],
    anonymous: false,
  },
  {
    type: "event",
    name: "DatasetMetadataUpdated",
    inputs: [
      { name: "id", type: "uint256", indexed: true },
      { name: "metadataURI", type: "string", indexed: false },
      { name: "updatedAt", type: "uint64", indexed: false },
    ],
    anonymous: false,
  },
] as const;

export const DATASET_NFT_ABI = [
  {
    type: "function",
    name: "mintDatasetNFT",
    stateMutability: "nonpayable",
    inputs: [
      { name: "datasetId", type: "uint256" },
      { name: "uri", type: "string" },
    ],
    outputs: [{ name: "tokenId", type: "uint256" }],
  },
  {
    type: "function",
    name: "ownerOf",
    stateMutability: "view",
    inputs: [{ name: "tokenId", type: "uint256" }],
    outputs: [{ name: "", type: "address" }],
  },
  {
    type: "function",
    name: "tokenURI",
    stateMutability: "view",
    inputs: [{ name: "tokenId", type: "uint256" }],
    outputs: [{ name: "", type: "string" }],
  },
  {
    type: "function",
    name: "minted",
    stateMutability: "view",
    inputs: [{ name: "", type: "uint256" }],
    outputs: [{ name: "", type: "bool" }],
  },
  {
    type: "event",
    name: "DatasetMinted",
    inputs: [
      { name: "tokenId", type: "uint256", indexed: true },
      { name: "datasetId", type: "uint256", indexed: true },
      { name: "owner", type: "address", indexed: true },
      { name: "storageRoot", type: "bytes32", indexed: false },
      { name: "tokenURI", type: "string", indexed: false },
      { name: "mintedAt", type: "uint64", indexed: false },
    ],
    anonymous: false,
  },
  {
    type: "event",
    name: "Transfer",
    inputs: [
      { name: "from", type: "address", indexed: true },
      { name: "to", type: "address", indexed: true },
      { name: "tokenId", type: "uint256", indexed: true },
    ],
    anonymous: false,
  },
] as const;

export const TRAINING_REGISTRY_ABI = [
  {
    type: "function",
    name: "createTrainingJob",
    stateMutability: "nonpayable",
    inputs: [
      { name: "datasetId", type: "uint256" },
      { name: "baseModel", type: "string" },
      { name: "configURI", type: "string" },
    ],
    outputs: [{ name: "id", type: "uint256" }],
  },
  {
    type: "function",
    name: "updateTrainingStatus",
    stateMutability: "nonpayable",
    inputs: [
      { name: "id", type: "uint256" },
      { name: "to", type: "uint8" },
    ],
    outputs: [],
  },
  {
    type: "function",
    name: "completeTrainingJob",
    stateMutability: "nonpayable",
    inputs: [
      { name: "id", type: "uint256" },
      { name: "finalStatus", type: "uint8" },
      { name: "checkpointRoot", type: "bytes32" },
    ],
    outputs: [],
  },
  {
    type: "event",
    name: "TrainingStarted",
    inputs: [
      { name: "id", type: "uint256", indexed: true },
      { name: "datasetId", type: "uint256", indexed: true },
      { name: "operator", type: "address", indexed: true },
      { name: "baseModel", type: "string", indexed: false },
      { name: "configURI", type: "string", indexed: false },
      { name: "createdAt", type: "uint64", indexed: false },
    ],
    anonymous: false,
  },
  {
    type: "event",
    name: "TrainingUpdated",
    inputs: [
      { name: "id", type: "uint256", indexed: true },
      { name: "status", type: "uint8", indexed: false },
      { name: "at", type: "uint64", indexed: false },
    ],
    anonymous: false,
  },
  {
    type: "event",
    name: "TrainingCompleted",
    inputs: [
      { name: "id", type: "uint256", indexed: true },
      { name: "status", type: "uint8", indexed: false },
      { name: "checkpointRoot", type: "bytes32", indexed: false },
      { name: "at", type: "uint64", indexed: false },
    ],
    anonymous: false,
  },
] as const;

export const USAGE_ECONOMY_ABI = [
  {
    type: "function",
    name: "feeFor",
    stateMutability: "view",
    inputs: [{ name: "", type: "uint8" }],
    outputs: [{ name: "", type: "uint256" }],
  },
  {
    type: "function",
    name: "payForAction",
    stateMutability: "payable",
    inputs: [
      { name: "kind", type: "uint8" },
      { name: "ref", type: "bytes32" },
    ],
    outputs: [{ name: "receiptId", type: "uint256" }],
  },
  {
    type: "event",
    name: "ActionPaid",
    inputs: [
      { name: "receiptId", type: "uint256", indexed: true },
      { name: "payer", type: "address", indexed: true },
      { name: "action", type: "uint8", indexed: true },
      { name: "ref", type: "bytes32", indexed: false },
      { name: "amount", type: "uint256", indexed: false },
      { name: "paidAt", type: "uint64", indexed: false },
    ],
    anonymous: false,
  },
] as const;

export enum UsageAction {
  PublishDataset = 0,
  StartTraining = 1,
  PremiumOp = 2,
}

export enum TrainingStatus {
  Pending = 0,
  Running = 1,
  Succeeded = 2,
  Failed = 3,
  Cancelled = 4,
}
