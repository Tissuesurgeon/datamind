"use client";

import { useCallback, useState } from "react";
import {
  parseEventLogs,
  type Address,
  type Hash,
  type Hex,
} from "viem";
import { toast } from "sonner";
import { useAccount, useChainId, useConfig } from "wagmi";
import {
  waitForTransactionReceipt,
  writeContract,
} from "wagmi/actions";

import { api } from "@/lib/api";
import { CONTRACTS } from "@/lib/web3/contracts";
import { OG_CHAIN_ID } from "@/lib/web3/networks";
import { bytes32, ensure0x } from "@/lib/web3/utils";
import { UsageAction } from "@/lib/web3/abi";
import type { DatasetDetail } from "@/types";
import type { TxState, TxStepProps } from "@/components/web3/TransactionStatus";

type ChainArgs = {
  storage_root: string;
  metadata_uri: string;
};

type PublishOptions = {
  /** Optional fee (in wei) to send for `UsageEconomy.payForAction(PublishDataset, ref)`. */
  publishFeeWei?: bigint;
  /** Override token URI for the NFT (defaults to the dataset's metadata URI). */
  tokenUri?: string;
};

/**
 * Drives the user-signed publishing flow:
 *
 *   1. (optional)  UsageEconomy.payForAction(PublishDataset, ref)
 *   2. DatasetRegistry.register(storageRoot, metadataURI)
 *   3. DatasetNFT.mintDatasetNFT(datasetId, tokenURI)
 *   4. POST /datasets/{id}/chain-confirm
 *
 * Each step exposes a `TxStepProps` via `steps` for use with `TransactionStatus`.
 */
export function useDatasetPublish() {
  const { address } = useAccount();
  const config = useConfig();
  const chainId = useChainId();
  const [steps, setSteps] = useState<TxStepProps[]>([]);
  const [busy, setBusy] = useState(false);

  const update = useCallback(
    (label: string, patch: Partial<Omit<TxStepProps, "label">>) => {
      setSteps((prev) => {
        const idx = prev.findIndex((s) => s.label === label);
        if (idx === -1) {
          return [...prev, { label, state: "idle", ...patch } as TxStepProps];
        }
        const next = [...prev];
        next[idx] = { ...next[idx], ...patch };
        return next;
      });
    },
    []
  );

  const reset = useCallback(() => setSteps([]), []);

  const publish = useCallback(
    async (
      datasetId: string,
      args: ChainArgs,
      opts: PublishOptions = {}
    ): Promise<DatasetDetail | null> => {
      if (!CONTRACTS.datasetRegistry.address || !CONTRACTS.datasetNft.address) {
        throw new Error(
          "Contracts not configured — set NEXT_PUBLIC_DATASET_REGISTRY / NEXT_PUBLIC_DATASET_NFT."
        );
      }
      if (!address) throw new Error("Connect a wallet first.");
      if (chainId !== OG_CHAIN_ID) {
        throw new Error(`Wrong network — switch to chain id ${OG_CHAIN_ID}.`);
      }

      toast.message("Approve in wallet", {
        description:
          "Your wallet will ask you to confirm register and mint transactions on 0G Galileo.",
      });

      setBusy(true);
      setSteps([]);

      const rootBytes32 = bytes32(args.storage_root) as Hex;
      const ref = bytes32(
        ("0x" + Buffer.from(datasetId, "utf-8").toString("hex"))
          .padEnd(66, "0")
          .slice(0, 66)
      ) as Hex;

      let registerTxHash: Hash | undefined;
      let mintTxHash: Hash | undefined;
      let onchainId: bigint | undefined;
      let tokenId: bigint | undefined;
      const tokenUri = opts.tokenUri ?? args.metadata_uri;

      try {
        // ---- 1. Optional publish fee --------------------------------------
        if (opts.publishFeeWei && CONTRACTS.usageEconomy.address) {
          const label = "Pay publish fee";
          update(label, { state: "pending" });
          const feeHash = await writeContract(config, {
            chainId: OG_CHAIN_ID,
            address: CONTRACTS.usageEconomy.address as Address,
            abi: CONTRACTS.usageEconomy.abi,
            functionName: "payForAction",
            args: [UsageAction.PublishDataset, ref],
            value: opts.publishFeeWei,
          });
          update(label, { state: "confirming", hash: feeHash });
          await waitForTransactionReceipt(config, {
            chainId: OG_CHAIN_ID,
            hash: feeHash,
          });
          update(label, { state: "success", hash: feeHash });
        }

        // ---- 2. Register the dataset on-chain -----------------------------
        const regLabel = "Register on DatasetRegistry";
        update(regLabel, { state: "pending" });
        registerTxHash = await writeContract(config, {
          chainId: OG_CHAIN_ID,
          address: CONTRACTS.datasetRegistry.address as Address,
          abi: CONTRACTS.datasetRegistry.abi,
          functionName: "register",
          args: [rootBytes32, args.metadata_uri],
        });
        update(regLabel, { state: "confirming", hash: registerTxHash });
        const regReceipt = await waitForTransactionReceipt(config, {
          chainId: OG_CHAIN_ID,
          hash: registerTxHash,
        });
        const regLogs = parseEventLogs({
          abi: CONTRACTS.datasetRegistry.abi,
          logs: regReceipt.logs,
          eventName: "DatasetRegistered",
        });
        onchainId = (regLogs[0]?.args as { id?: bigint } | undefined)?.id;
        update(regLabel, { state: "success", hash: registerTxHash });
        if (onchainId === undefined) {
          throw new Error("DatasetRegistered event not found in receipt.");
        }

        // ---- 3. Mint the NFT (tokenId mirrors onchainId) ------------------
        const mintLabel = "Mint Dataset NFT";
        update(mintLabel, { state: "pending" });
        mintTxHash = await writeContract(config, {
          chainId: OG_CHAIN_ID,
          address: CONTRACTS.datasetNft.address as Address,
          abi: CONTRACTS.datasetNft.abi,
          functionName: "mintDatasetNFT",
          args: [onchainId, tokenUri],
        });
        update(mintLabel, { state: "confirming", hash: mintTxHash });
        const mintReceipt = await waitForTransactionReceipt(config, {
          chainId: OG_CHAIN_ID,
          hash: mintTxHash,
        });
        const mintLogs = parseEventLogs({
          abi: CONTRACTS.datasetNft.abi,
          logs: mintReceipt.logs,
          eventName: "DatasetMinted",
        });
        tokenId =
          (mintLogs[0]?.args as { tokenId?: bigint } | undefined)?.tokenId ??
          onchainId;
        update(mintLabel, { state: "success", hash: mintTxHash });

        // ---- 4. Notify backend so the row flips to READY ------------------
        const apiLabel = "Notify DataMind backend";
        update(apiLabel, { state: "pending" });
        const detail = await api.post<DatasetDetail>(
          `/datasets/${datasetId}/chain-confirm`,
          {
            onchain_id: Number(onchainId),
            token_id: tokenId !== undefined ? Number(tokenId) : null,
            register_tx_hash: registerTxHash,
            mint_tx_hash: mintTxHash,
            nft_contract: CONTRACTS.datasetNft.address,
            chain_id: OG_CHAIN_ID,
          }
        );
        update(apiLabel, { state: "success" });
        return detail;
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Transaction failed";
        // Mark the last pending step as errored so the UI matches reality.
        setSteps((prev) => {
          const next = [...prev];
          for (let i = next.length - 1; i >= 0; i--) {
            if (next[i].state === "pending" || next[i].state === "confirming") {
              next[i] = { ...next[i], state: "error", error: msg };
              break;
            }
          }
          return next;
        });
        throw err;
      } finally {
        setBusy(false);
      }
    },
    [address, chainId, config, update]
  );

  return { publish, steps, busy, reset };
}

/** Convenience for callers that want the same shape outside hooks. */
export type DatasetPublishStep = TxStepProps;
export type DatasetPublishState = TxState;
export { ensure0x };
