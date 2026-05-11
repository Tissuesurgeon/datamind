"use client";

import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useAccount } from "wagmi";

import { useBackendChainConfig, useDataset } from "@/lib/queries";
import { useDatasetPublish } from "@/hooks/useDatasetPublish";
import { PUBLISH_CONTRACTS_READY } from "@/lib/web3/contracts";
import { OG_CHAIN_ID } from "@/lib/web3/networks";
import { WalletConnect } from "@/components/web3/WalletConnect";
import { TransactionStatus } from "@/components/web3/TransactionStatus";

/**
 * When a dataset is stuck in `pending_chain`, resume the wagmi register + mint flow
 * (e.g. user reloaded or switched tabs and missed the upload WebSocket).
 */
export function PendingChainContinue({ datasetId }: { datasetId: string }) {
  const router = useRouter();
  const qc = useQueryClient();
  const { data: cfg } = useBackendChainConfig();
  const { data: detail } = useDataset(datasetId, { refetchWhileProcessing: true });
  const { isConnected } = useAccount();
  const publishHook = useDatasetPublish();
  const startedRef = useRef(false);

  const args = detail?.pending_chain_args;
  const isPending = detail?.status === "pending_chain" && cfg?.web3_user_tx;

  useEffect(() => {
    startedRef.current = false;
  }, [datasetId]);

  useEffect(() => {
    if (!isPending || !args?.storage_root || !args?.metadata_uri) return;
    if (!PUBLISH_CONTRACTS_READY) return;
    if (!isConnected) return;
    if (startedRef.current) return;
    startedRef.current = true;
    void publishHook
      .publish(datasetId, args)
      .then(() => {
        toast.success("Dataset minted + registered on-chain");
        void qc.invalidateQueries({ queryKey: ["dataset", datasetId] });
        router.refresh();
      })
      .catch((err) => {
        startedRef.current = false;
        toast.error(err instanceof Error ? err.message : "On-chain publish failed");
      });
  }, [isPending, args, isConnected, datasetId, publishHook, router, qc]);

  if (!isPending) return null;

  return (
    <div className="rounded-2xl border border-amber-500/35 bg-amber-500/10 p-5 text-sm">
      <p className="font-medium text-amber-100">Awaiting your wallet</p>
      <p className="mt-2 text-xs text-amber-100/85">
        If nothing pops up, check the wallet extension and network (Galileo, chain id {OG_CHAIN_ID}).
      </p>
      {!PUBLISH_CONTRACTS_READY && (
        <p className="mt-2 text-xs text-amber-200/90">
          Set <code className="rounded bg-black/30 px-1">NEXT_PUBLIC_DATASET_REGISTRY</code> and{" "}
          <code className="rounded bg-black/30 px-1">NEXT_PUBLIC_DATASET_NFT</code>, then rebuild the frontend.
        </p>
      )}
      {PUBLISH_CONTRACTS_READY && !isConnected && (
        <div className="mt-4">
          <WalletConnect />
        </div>
      )}
      {publishHook.steps.length > 0 && (
        <div className="mt-4">
          <TransactionStatus steps={publishHook.steps} />
        </div>
      )}
    </div>
  );
}
