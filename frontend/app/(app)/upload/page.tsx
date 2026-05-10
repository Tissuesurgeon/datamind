"use client";

import { useCallback, useEffect, useState } from "react";
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
import { useUploadDataset } from "@/lib/queries";
import { useAuthHelpers } from "@/lib/privy";
import { useLiveTopic } from "@/hooks/useLiveTopic";
import { compactNumber } from "@/lib/utils";

const CATEGORIES = ["Web3", "NLP", "Finance", "Tabular", "Vision", "Audio", "Other"];

export default function UploadPage() {
  const router = useRouter();
  const { authenticated, requireAuth, signIn } = useAuthHelpers();
  const upload = useUploadDataset();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("Web3");
  const [tags, setTags] = useState("");
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [progressLine, setProgressLine] = useState("Waiting…");

  const { events } = useLiveTopic(datasetId ? `dataset:${datasetId}` : null);

  // Watch ws events for progress + redirect on completion.
  useEffect(() => {
    if (!datasetId || events.length === 0) return;
    const last = events[events.length - 1];
    setProgressLine(`${last.type} · ${JSON.stringify(last.payload).slice(0, 80)}`);
    if (last.type === "upload.completed") {
      toast.success("Dataset processed and anchored");
      router.push(`/datasets/${datasetId}`);
    }
  }, [events, datasetId, router]);

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
    if (!authenticated) await signIn();
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

          <Button
            disabled={!file || upload.isPending}
            onClick={async () => {
              await requireAuth();
              await submit();
            }}
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
        <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5">
          <div className="text-xs uppercase tracking-wider text-text-dim">
            Live processing
          </div>
          <div className="mt-3 font-mono text-sm">{progressLine}</div>
          <Progress value={numericProgress} className="mt-3" />
        </div>

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
              "Anchor in DatasetRegistry.sol",
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
