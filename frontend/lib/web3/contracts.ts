import type { Address } from "viem";

import {
  DATASET_NFT_ABI,
  DATASET_REGISTRY_ABI,
  TRAINING_REGISTRY_ABI,
  USAGE_ECONOMY_ABI,
} from "./abi";
import { isAddress } from "./utils";

const ENV = {
  registry: process.env.NEXT_PUBLIC_DATASET_REGISTRY || "",
  nft:      process.env.NEXT_PUBLIC_DATASET_NFT      || "",
  training: process.env.NEXT_PUBLIC_TRAINING_REGISTRY || "",
  economy:  process.env.NEXT_PUBLIC_USAGE_ECONOMY    || "",
  license:  process.env.NEXT_PUBLIC_LICENSE_REGISTRY || "",
};

function asAddress(v: string): Address | undefined {
  return isAddress(v) ? (v as Address) : undefined;
}

export const CONTRACTS = {
  datasetRegistry: {
    address: asAddress(ENV.registry),
    abi: DATASET_REGISTRY_ABI,
  },
  datasetNft: {
    address: asAddress(ENV.nft),
    abi: DATASET_NFT_ABI,
  },
  trainingRegistry: {
    address: asAddress(ENV.training),
    abi: TRAINING_REGISTRY_ABI,
  },
  usageEconomy: {
    address: asAddress(ENV.economy),
    abi: USAGE_ECONOMY_ABI,
  },
  licenseRegistry: {
    address: asAddress(ENV.license),
  },
} as const;

/** Registry + DatasetNFT only — enough for the upload / mint flow. */
export const PUBLISH_CONTRACTS_READY =
  Boolean(CONTRACTS.datasetRegistry.address) &&
  Boolean(CONTRACTS.datasetNft.address);

/** True when every protocol contract has a usable address configured. */
export const CONTRACTS_READY =
  Boolean(CONTRACTS.datasetRegistry.address) &&
  Boolean(CONTRACTS.datasetNft.address) &&
  Boolean(CONTRACTS.trainingRegistry.address) &&
  Boolean(CONTRACTS.usageEconomy.address);
