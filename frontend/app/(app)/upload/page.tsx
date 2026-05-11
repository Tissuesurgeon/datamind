"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import { CheckCircle2, FileText, Loader2, UploadCloud } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUploadDataset, useBackendChainConfig, useDataset } from "@/lib/queries";
import { useAuthHelpers } from "@/lib/privy";
import { useAuthStore } from "@/lib/auth-store";
import { useLiveTopic } from "@/hooks/useLiveTopic";
import { useDatasetPublish } from "@/hooks/useDatasetPublish";
import { compactNumber } from "@/lib/utils";
import { TransactionStatus } from "@/components/web3/TransactionStatus";
import { NetworkSwitcher } from "@/components/web3/NetworkSwitcher";
import { ChainModeBanner } from "@/components/web3/ChainModeBanner";
import { WalletConnect } from "@/components/web3/WalletConnect";
import { PUBLISH_CONTRACTS_READY } from "@/lib/web3/contracts";
import { useAccount } from "wagmi";

const CATEGORIES = ["Web3", "NLP", "Finance", "Tabular", "Vision", "Audio", "Other"];

const LICENSE_OPTIONS: { value: string; label: string }[] = [
  { value: "none", label: "Not specified" },
  { value: "personal", label: "Personal" },
  { value: "commercial", label: "Commercial" },
  { value: "academic", label: "Academic" },
  { value: "exclusive", label: "Exclusive" },
];

export default function UploadPage() {
  const router = useRouter();
  const { requireAuth } = useAuthHelpers();
  const upload = useUploadDataset();
  const publishHook = useDatasetPublish();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("Web3");
  const [tags, setTags] = useState("");
  /** Empty string = free listing; otherwise parsed as OG amount for marketplace metadata. */
  const [priceOg, setPriceOg] = useState("");
  const [licenseKind, setLicenseKind] = useState<string>("none");
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [progressLine, setProgressLine] = useState("Waiting…");
  const publishedRef = useRef(false);
  const contractWarnedRef = useRef(false);
  const walletWarnedRef = useRef(false);

  const { data: chainCfg } = useBackendChainConfig();
  const { data: datasetDetail } = useDataset(datasetId, {
    refetchWhileProcessing: true,
  });
  const { isConnected } = useAccount();

  const { events } = useLiveTopic(datasetId ? `dataset:${datasetId}` : null);

  useEffect(() => {
    publishedRef.current = false;
    contractWarnedRef.current = false;
    walletWarnedRef.current = false;
  }, [datasetId]);

  const startPublish = useCallback(
    (id: string, chainArgs: { storage_root: string; metadata_uri: string }) => {
      if (!chainCfg?.web3_user_tx) return;
      if (!PUBLISH_CONTRACTS_READY) return;
      if (!isConnected) {
        if (!walletWarnedRef.current) {
          walletWarnedRef.current = true;
          toast.warning("Connect your wallet (top right) to approve on-chain transactions.");
        }
        return;
      }
      if (publishedRef.current) return;
      publishedRef.current = true;
      void publishHook
        .publish(id, chainArgs)
        .then(() => {
          toast.success("Dataset minted + registered on-chain");
          router.push(`/datasets/${id}`);
        })
        .catch((err) => {
          publishedRef.current = false;
          toast.error(err instanceof Error ? err.message : "On-chain publish failed");
        });
    },
    [chainCfg?.web3_user_tx, isConnected, publishHook, router]
  );

  // Poll API fallback: WebSocket may miss storage.anchored if the client connects late.
  useEffect(() => {
    if (!datasetId || !datasetDetail) return;
    if (datasetDetail.status !== "pending_chain") return;
    const args = datasetDetail.pending_chain_args;
    if (!args?.storage_root || !args?.metadata_uri) return;
    startPublish(datasetId, args);
  }, [datasetId, datasetDetail, startPublish]);

  useEffect(() => {
    if (!datasetId || !datasetDetail || datasetDetail.status !== "pending_chain") return;
    if (!chainCfg?.web3_user_tx) return;
    if (PUBLISH_CONTRACTS_READY || contractWarnedRef.current) return;
    contractWarnedRef.current = true;
    toast.error(
      "Wallet signing is on, but contract addresses are missing. Set NEXT_PUBLIC_DATASET_REGISTRY and NEXT_PUBLIC_DATASET_NFT, then redeploy the frontend."
    );
  }, [datasetId, datasetDetail, chainCfg?.web3_user_tx]);

  // Watch ws events for progress + handle pending_chain + redirect on completion.
  useEffect(() => {
    if (!datasetId || events.length === 0) return;
    const last = events[events.length - 1];
    setProgressLine(`${last.type} · ${JSON.stringify(last.payload).slice(0, 80)}`);

    const pending =
      last.type === "storage.anchored" &&
      Boolean((last.payload as Record<string, unknown>)?.pending_chain);
    if (pending) {
      const payload = last.payload as Record<string, unknown>;
      const chainArgs = (payload.chain_args as
        | { storage_root: string; metadata_uri: string }
        | undefined) ?? {
        storage_root: String(payload.storage_root || ""),
        metadata_uri: String(payload.metadata_uri || ""),
      };
      startPublish(datasetId, chainArgs);
    }

    if (last.type === "upload.completed") {
      const skippedChain = Boolean(
        (last.payload as Record<string, unknown>)?.pending_chain
      );
      if (!skippedChain) {
        toast.success("Dataset processed and anchored");
        router.push(`/datasets/${datasetId}`);
      }
    }
  }, [events, datasetId, router, startPublish]);

  const onDrop = useCallback((accepted: File[]) => {
    const f = accepted[0];
    if (!f) return;
    setFile(f);
    if (!title) setTitle(f.name.replace(/\.[^.]+$/, ""));
  }, [title]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "text/csv": [".csv"],
      "application/json": [".json", ".jsonl"],
      "text/plain": [".txt"],
      "application/pdf": [".pdf"],
      "text/tab-separated-values": [".tsv"],
    },
    maxSize: 200 * 1024 * 1024,
  });

  const submit = async () => {
    if (!file) return;
    await requireAuth();
    const token = useAuthStore.getState().token;
    if (!token) {
      toast.error("Session not ready — connect wallet or wait a moment and retry.");
      return;
    }
    const fd = new FormData();
    fd.append("file", file);
    fd.append("title", title || file.name);
    if (description) fd.append("description", description);
    fd.append("category", category);
    fd.append(
      "tags",
      JSON.stringify(
        tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean)
      )
    );
    fd.append("visibility", "public");
    const priceParsed = parseFloat(priceOg.replace(/,/g, "").trim());
    if (priceOg.trim() !== "" && !Number.isNaN(priceParsed) && priceParsed >= 0) {
      fd.append("price_amount", String(priceParsed));
    }
    if (licenseKind && licenseKind !== "none") {
      fd.append("license_kind", licenseKind);
    }
    try {
      const res = await upload.mutateAsync(fd);
      setDatasetId(res.dataset.id);
      setProgressLine("Uploaded — waiting for AI pipeline…");
      toast.success("Upload accepted");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Upload failed");
    }
  };

  const lastProgress =
    events.find((e) => typeof e.payload?.progress === "number")?.payload?.progress;
  const numericProgress = (datasetId ? Number(lastProgress ?? 5) : 0) || 0;

  return (
    <div className="grid gap-8 lg:grid-cols-[1.4fr_1fr]">
      <div className="space-y-6">
        <ChainModeBanner />
        <header>
          <h1 className="text-3xl font-medium tracking-tight">Upload a dataset</h1>
          <p className="mt-1 text-sm text-text-muted">
            Drop any CSV / JSON / TXT / PDF — DataMind will analyze, embed,
            score, and anchor it on 0G.
          </p>
        </header>

        <div
          {...getRootProps()}
          className={
            "relative cursor-pointer rounded-2xl border-2 border-dashed bg-surface-1 p-10 text-center transition-all " +
            (isDragActive
              ? "border-brand-amber-500 bg-brand-amber-500/5"
              : "border-border-subtle hover:border-border-strong")
          }
        >
          <input {...getInputProps()} />
          <UploadCloud className="mx-auto h-10 w-10 text-text-dim" />
          <div className="mt-3 text-base font-medium">
            {file ? file.name : "Drop a file here or click to browse"}
          </div>
          <div className="mt-1 text-xs text-text-dim">
            CSV · JSON · JSONL · TXT · PDF · TSV up to 200 MB
          </div>
          {file && (
            <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-border-subtle bg-surface-2 px-3 py-1 text-xs">
              <FileText className="h-3.5 w-3.5" /> {compactNumber(file.size)} bytes
            </div>
          )}
        </div>

        <div className="space-y-4 rounded-2xl border border-border-subtle bg-surface-1 p-5">
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wider text-text-dim">
                Title
              </label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wider text-text-dim">
                Category
              </label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs uppercase tracking-wider text-text-dim">
              Tags (comma-separated)
            </label>
            <Input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="sentiment, twitter, crypto"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs uppercase tracking-wider text-text-dim">
              Description
            </label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's in this dataset and how should buyers use it?"
              rows={4}
            />
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wider text-text-dim">
                Price (OG, optional)
              </label>
              <Input
                inputMode="decimal"
                type="text"
                value={priceOg}
                onChange={(e) => setPriceOg(e.target.value)}
                placeholder="0 = free"
              />
              <p className="mt-1 text-[11px] text-text-dim">
                Stored for marketplace display; on-chain settlement is not enforced by this UI.
              </p>
            </div>
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wider text-text-dim">
                License
              </label>
              <Select value={licenseKind} onValueChange={setLicenseKind}>
                <SelectTrigger>
                  <SelectValue placeholder="License type" />
                </SelectTrigger>
                <SelectContent>
                  {LICENSE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            disabled={!file || upload.isPending}
            onClick={() => void submit()}
            className="w-full"
            size="lg"
            variant="gradient"
          >
            {upload.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Uploading…
              </>
            ) : (
              <>
                <UploadCloud className="h-4 w-4" /> Upload & process
              </>
            )}
          </Button>
        </div>
      </div>

      <aside className="space-y-4">
        <NetworkSwitcher />

        {chainCfg?.web3_user_tx &&
          datasetDetail?.status === "pending_chain" &&
          !isConnected && (
            <div className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-5 text-sm text-amber-100">
              <p className="font-medium">Wallet required</p>
              <p className="mt-2 text-xs text-amber-100/85">
                Connect the same wallet you use in the app so MetaMask (or your wallet) can
                prompt for <strong>register</strong> and <strong>mint</strong>.
              </p>
              <div className="mt-3">
                <WalletConnect />
              </div>
            </div>
          )}
        <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5">
          <div className="text-xs uppercase tracking-wider text-text-dim">
            Live processing
          </div>
          <div className="mt-3 font-mono text-sm">{progressLine}</div>
          <Progress value={numericProgress} className="mt-3" />
        </div>

        {publishHook.steps.length > 0 && (
          <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5">
            <div className="text-xs uppercase tracking-wider text-text-dim">
              On-chain publish
            </div>
            <div className="mt-3">
              <TransactionStatus steps={publishHook.steps} />
            </div>
          </div>
        )}

        <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5 text-xs text-text-muted">
          <div className="mb-2 text-text-dim uppercase tracking-wider">
            Pipeline stages
          </div>
          <ul className="space-y-1.5">
            {[
              "Validate format & size",
              "Extract metadata",
              "AI quality + tagging",
              "Embed + index in Qdrant",
              "Push to 0G Storage",
              "User wallet mints DatasetNFT",
              "User wallet anchors in DatasetRegistry.sol",
            ].map((s, i) => {
              const seen = events.length > 0 && i * 16 <= numericProgress;
              return (
                <li key={s} className="flex items-center gap-2">
                  <CheckCircle2
                    className={
                      "h-3.5 w-3.5 " +
                      (seen ? "text-brand-amber-300" : "text-text-dim")
                    }
                  />
                  <span className={seen ? "text-text" : ""}>{s}</span>
                </li>
              );
            })}
          </ul>
        </div>
      </aside>
    </div>
  );
}
