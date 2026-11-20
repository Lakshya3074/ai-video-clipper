import { useState } from "react";
import { Download, Mic, Brain, Film, CheckCircle, AlertCircle, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface JobProgressProps {
  job: {
    jobId: string;
    status: string;
    progress: number;
    currentStep: string;
    detail?: string;
    clips: Array<{ id: string; title: string; virality_score: number }>;
    error?: string;
  } | null;
}

const STEPS = [
  { id: "downloading", label: "Downloading", icon: Download },
  { id: "transcribing", label: "Transcribing", icon: Mic },
  { id: "analyzing", label: "Analyzing", icon: Brain },
  { id: "rendering", label: "Rendering", icon: Film },
] as const;

export function JobProgress({ job }: JobProgressProps) {
  const [expanded, setExpanded] = useState(true);

  if (!job) return null;

  const currentStepIndex = STEPS.findIndex((s) => s.id === job.status);
  const completedSteps = currentStepIndex >= 0 ? currentStepIndex : STEPS.length;

  return (
    <div className="flex-1 overflow-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg">Progress</h3>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-muted-foreground hover:text-foreground p-1 no-drag"
        >
          {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {expanded && (
        <>
          <div className="space-y-3">
            {STEPS.map((step, index) => {
              const isComplete = index < completedSteps;
              const isCurrent = index === currentStepIndex && job.status !== "completed" && job.status !== "failed";
              const Icon = step.icon;

              return (
                <div
                  key={step.id}
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-lg transition-all",
                    isComplete
                      ? "bg-green-400/10 border border-green-400/20"
                      : isCurrent
                      ? "bg-primary/10 border border-primary/20"
                      : "bg-muted/30 border border-border"
                  )}
                >
                  <div
                    className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                      isComplete
                        ? "bg-green-400 text-background"
                        : isCurrent
                        ? "bg-primary text-primary-foreground animate-pulse"
                        : "bg-muted text-muted-foreground"
                    )}
                  >
                    {isComplete ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : isCurrent ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Icon className="w-5 h-5" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={cn("font-medium truncate", isCurrent ? "text-primary" : "")}>
                      {step.label}
                    </p>
                    {isCurrent && job.detail && (
                      <p className="text-xs text-muted-foreground truncate">{job.detail}</p>
                    )}
                  </div>
                  {isCurrent && (
                    <span className="text-sm font-mono text-primary">{job.progress}%</span>
                  )}
                </div>
              );
            })}

            {job.status === "completed" && job.clips.length > 0 && (
              <div className="flex items-center gap-3 p-3 rounded-lg bg-green-400/10 border border-green-400/20">
                <CheckCircle className="w-8 h-8 text-green-400 flex-shrink-0" />
                <div>
                  <p className="font-medium text-green-400">Analysis Complete!</p>
                  <p className="text-sm text-muted-foreground">
                    Found {job.clips.length} viral clip{job.clips.length !== 1 ? "s" : ""}
                  </p>
                </div>
              </div>
            )}

            {job.status === "failed" && (
              <div className="flex items-center gap-3 p-3 rounded-lg bg-red-400/10 border border-red-400/20">
                <AlertCircle className="w-8 h-8 text-red-400 flex-shrink-0" />
                <div>
                  <p className="font-medium text-red-400">Processing Failed</p>
                  <p className="text-sm text-muted-foreground">{job.error || "Unknown error"}</p>
                </div>
              </div>
            )}
          </div>

          <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-500",
                job.status === "failed" ? "bg-red-400" : "bg-primary"
              )}
              style={{ width: `${job.progress}%` }}
            />
          </div>
        </>
      )}
    </div>
  );
}