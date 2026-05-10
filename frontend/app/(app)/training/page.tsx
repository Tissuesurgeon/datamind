"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2, Workflow } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { LogStream } from "@/components/datamind/log-stream";
import { TrainingChart } from "@/components/datamind/training-chart";
import { useCreateTraining, useDatasets, useTrainingJob, useTrainingJobs } from "@/lib/queries";
import { useAuthHelpers } from "@/lib/privy";
import { useLiveTopic } from "@/hooks/useLiveTopic";
import { cn } from "@/lib/utils";

const MODELS = [
  "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "distilbert-base-uncased",
  "microsoft/phi-1_5",
  "Qwen/Qwen2.5-0.5B",
];

export default function TrainingPage() {
  const search = useSearchParams();
  const presetDataset = search.get("dataset");
  const presetJob = search.get("id");

  const { data: datasetsPage } = useDatasets({});
  const { data: jobs } = useTrainingJobs();
  const create = useCreateTraining();
  const { requireAuth } = useAuthHelpers();

  const [datasetId, setDatasetId] = useState<string>(presetDataset || "");
  const [name, setName] = useState("Crypto sentiment LoRA");
  const [model, setModel] = useState(MODELS[0]);
  const [epochs, setEpochs] = useState(3);
  const [lr, setLr] = useState(0.0002);

  const [activeJobId, setActiveJobId] = useState<string | null>(presetJob);

  // When the dataset list loads and no preset is set, default to the first.
  useEffect(() => {
    if (!datasetId && datasetsPage?.items?.length) {
      setDatasetId(datasetsPage.items[0].id);
    }
  }, [datasetsPage, datasetId]);

  const { data: job } = useTrainingJob(activeJobId);
  const { events } = useLiveTopic(activeJobId ? `training:${activeJobId}` : null);

  const history = useMemo(() => {
    const fromMetrics = (job?.metrics?.history as any[]) || [];
    const fromWs = events
      .filter((e) => e.type === "train.progress")
      .map((e) => e.payload as any);
    const merged = [...fromMetrics, ...fromWs];
    // Deduplicate by step
    const seen = new Set<number>();
    return merged.filter((p) => {
      if (seen.has(p.step)) return false;
      seen.add(p.step);
      return true;
    });
  }, [job, events]);

  const launch = async () => {
    if (!datasetId) {
      toast.error("Pick a dataset first");
      return;
    }
    await requireAuth();
    try {
      const res = await create.mutateAsync({
        dataset_id: datasetId,
        name: name || "Untitled run",
        base_model: model,
        epochs,
        batch_size: 4,
        learning_rate: lr,
        lora_r: 8,
        lora_alpha: 16,
        max_seq_length: 512,
      });
      setActiveJobId(res.id);
      toast.success("Training launched");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Launch failed");
    }
  };

  const progress = (job?.progress ?? 0) as number;

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_1.4fr]">
      <div className="space-y-4">
        <header>
          <h1 className="text-3xl font-medium tracking-tight">Training studio</h1>
          <p className="mt-1 text-sm text-text-muted">
            Lightweight LoRA fine-tuning. Live metrics over WebSocket.
          </p>
        </header>

        <div className="space-y-3 rounded-2xl border border-border-subtle bg-surface-1 p-5">
          <Field label="Dataset">
            <Select value={datasetId} onValueChange={setDatasetId}>
              <SelectTrigger>
                <SelectValue placeholder="Pick a dataset" />
              </SelectTrigger>
              <SelectContent>
                {(datasetsPage?.items || []).map((d) => (
                  <SelectItem key={d.id} value={d.id}>
                    {d.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label="Run name">
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
          <Field label="Base model">
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MODELS.map((m) => (
                  <SelectItem key={m} value={m}>
                    {m}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Epochs">
              <Input
                type="number"
                value={epochs}
                onChange={(e) => setEpochs(parseInt(e.target.value || "1"))}
                min={1}
                max={10}
              />
            </Field>
            <Field label="Learning rate">
              <Input
                type="number"
                step="0.0001"
                value={lr}
                onChange={(e) => setLr(parseFloat(e.target.value || "0.0002"))}
              />
            </Field>
          </div>

          <Button
            onClick={launch}
            className="w-full"
            size="lg"
            variant="gradient"
            disabled={create.isPending || !datasetId}
          >
            {create.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Launching…
              </>
            ) : (
              <>
                <Workflow className="h-4 w-4" /> Launch fine-tune
              </>
            )}
          </Button>
        </div>

        <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5">
          <div className="text-xs uppercase tracking-wider text-text-dim">
            Recent runs
          </div>
          <ul className="mt-3 divide-y divide-border-subtle">
            {(jobs || []).slice(0, 8).map((j) => (
              <li
                key={j.id}
                className={cn(
                  "flex items-center justify-between gap-2 py-2 text-sm",
                  j.id === activeJobId && "text-brand-amber-300"
                )}
              >
                <button
                  onClick={() => setActiveJobId(j.id)}
                  className="flex-1 truncate text-left hover:text-text"
                >
                  {j.name}
                </button>
                <span className="text-xs text-text-dim">{j.status}</span>
              </li>
            ))}
            {!jobs?.length && (
              <li className="py-3 text-center text-xs text-text-dim">No runs yet.</li>
            )}
          </ul>
        </div>
      </div>

      <div className="space-y-4">
        <div className="rounded-2xl border border-border-subtle bg-surface-1 p-5">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-wider text-text-dim">
                Active run
              </div>
              <div className="mt-1 truncate text-sm">
                {job?.name || "—"}{" "}
                <span className="text-text-dim">· {job?.base_model || "—"}</span>
              </div>
            </div>
            <div className="font-mono text-sm">
              {progress.toFixed(1)}%
            </div>
          </div>
          <Progress value={progress} className="mt-3" />
          {job && (
            <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
              <Mini
                label="Loss"
                value={
                  history.length
                    ? history[history.length - 1].loss?.toFixed(4) || "—"
                    : "—"
                }
              />
              <Mini label="Epoch" value={String(job.epoch ?? 0)} />
              <Mini label="Status" value={job.status} />
            </div>
          )}
        </div>

        <TrainingChart data={history as any} />
        <LogStream events={events} />
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-xs uppercase tracking-wider text-text-dim">
        {label}
      </label>
      {children}
    </div>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border-subtle bg-surface-2 px-3 py-2">
      <div className="font-mono text-sm text-text">{value}</div>
      <div className="text-text-dim">{label}</div>
    </div>
  );
}
