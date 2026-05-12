import { Suspense } from "react";
import { Loader2 } from "lucide-react";

import { TrainingStudioClient } from "./training-studio-client";

export default function TrainingPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[40vh] flex-col items-center justify-center gap-2 text-sm text-text-muted">
          <Loader2 className="h-8 w-8 animate-spin opacity-80" aria-hidden />
          <span>Loading training studio…</span>
        </div>
      }
    >
      <TrainingStudioClient />
    </Suspense>
  );
}
