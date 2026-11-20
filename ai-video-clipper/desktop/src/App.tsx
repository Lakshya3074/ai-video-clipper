import { useState, useEffect, useRef, useCallback } from "react";
import { invoke, invokeSidecar } from "@tauri-apps/plugin-shell";
import { open } from "@tauri-apps/plugin-dialog";
import { UploadArea } from "./components/UploadArea";
import { ClipStudio } from "./components/ClipStudio";
import { Header } from "./components/Header";
import { JobProgress } from "./components/JobProgress";
import { Toast } from "./components/Toast";
import { cn } from "./lib/utils";

interface BackendStatus {
  running: boolean;
  port: number;
  url: string;
}

interface ViralClip {
  id: string;
  title: string;
  hook_reasoning: string;
  virality_score: number;
  start_time: number;
  end_time: number;
  duration: number;
  transcript: string;
}

interface JobData {
  jobId: string;
  status: string;
  progress: number;
  currentStep: string;
  detail?: string;
  clips: ViralClip[];
  error?: string;
}

export default function App() {
  const [backendUrl, setBackendUrl] = useState("");
  const [backendStatus, setBackendStatus] = useState<BackendStatus | null>(null);
  const [job, setJob] = useState<JobData | null>(null);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);
  const [loading, setLoading] = useState(true);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const showToast = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  }, []);

  // Check backend status on mount
  useEffect(() => {
    (async () => {
      try {
        const status: BackendStatus = await invoke("get_backend_status");
        setBackendStatus(status);
        setBackendUrl(`http://localhost:${status.port}`);
      } catch (e) {
        console.error("Backend check failed:", e);
      }
      setLoading(false);
    })();
  }, []);

  const connectWebSocket = useCallback((jobId: string) => {
    const ws = new WebSocket(`${backendUrl.replace("http", "ws")}/jobs/${jobId}/ws`);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setJob((prev) => prev ? { ...prev, ...data } : data);
        if (data.status === "completed") {
          showToast(`Found ${data.clips?.length || 0} viral clips!`, "success");
        }
        if (data.status === "failed") {
          showToast(data.error || "Processing failed", "error");
        }
      } catch (e) {
        // Parse error
      }
    };
    ws.onclose = () => {
      // Fallback to polling
      startPolling(jobId);
    };
    ws.onerror = () => {
      startPolling(jobId);
    };
    return ws;
  }, [backendUrl, showToast]);

  const startPolling = useCallback((jobId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${backendUrl}/jobs/${jobId}/progress`);
        if (res.ok) {
          const data = await res.json();
          setJob((prev) => prev ? { ...prev, ...data } : data);
          if (data.status === "completed" || data.status === "failed") {
            if (pollingRef.current) clearInterval(pollingRef.current);
          }
        }
      } catch (e) {
        // Ignore polling errors
      }
    }, 1000);
  }, [backendUrl]);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) clearInterval(pollingRef.current);
  }, []);

  const handleFileUpload = async (file: File | null) => {
    if (!file) return;

    try {
      // Read file data
      const buffer = await file.arrayBuffer();
      const bytes = Array.from(new Uint8Array(buffer));

      const formData = new FormData();
      formData.append("source_type", "upload");
      formData.append("file", file);

      const res = await fetch(`${backendUrl}/jobs`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to create job");
      const data = await res.json();
      setJob({
        jobId: data.job_id,
        status: "processing",
        progress: 0,
        currentStep: "Queued",
        clips: [],
      });
      connectWebSocket(data.job_id);
      showToast("Job started! Processing video...", "success");
    } catch (e) {
      showToast("Failed: " + (e as Error).message, "error");
    }
  };

  const handleUrlUpload = async (url: string) => {
    try {
      const formData = new FormData();
      formData.append("source_type", "url");
      formData.append("url", url);

      const res = await fetch(`${backendUrl}/jobs`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to create job");
      const data = await res.json();
      setJob({
        jobId: data.job_id,
        status: "processing",
        progress: 0,
        currentStep: "Queued",
        clips: [],
      });
      connectWebSocket(data.job_id);
      showToast("Job started! Downloading video...", "success");
    } catch (e) {
      showToast("Failed: " + (e as Error).message, "error");
    }
  };

  const handleRender = async (clips: ViralClip[]) => {
    if (!job) return;
    try {
      const res = await fetch(`${backendUrl}/jobs/${job.jobId}/render`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: job.jobId, clips }),
      });
      if (!res.ok) throw new Error("Render failed");
      showToast("Rendering started!", "success");
    } catch (e) {
      showToast("Render failed: " + (e as Error).message, "error");
    }
  };

  const handlePickFile = async () => {
    try {
      const selected = await open({
        multiple: false,
        directory: false,
        filters: [
          {
            name: "Video Files",
            extensions: ["mp4", "mov", "mkv", "webm", "avi", "flv"],
          },
        ],
      });
      if (selected) {
        const fileHandle = selected as File;
        // For Tauri file picker, we need to pass the path
        handleFileUpload(fileHandle as any);
      }
    } catch (e) {
      console.error("File picker error:", e);
    }
  };

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading AI Video Clipper...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <main className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        <aside className="w-full lg:w-96 border-r border-border bg-card flex flex-col">
          <UploadArea
            onFileUpload={handleFileUpload}
            onUrlUpload={handleUrlUpload}
            onPickFile={handlePickFile}
            disabled={!!job}
          />
          <JobProgress job={job} />
        </aside>
        <section className="flex-1 overflow-auto p-4 lg:p-6">
          {job && job.clips.length > 0 && (
            <ClipStudio
              jobId={job.jobId}
              clips={job.clips}
              status={job.status}
              onRender={handleRender}
              apiBase={backendUrl}
            />
          )}
          {!job && (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
              <div className="text-6xl mb-4">🎬</div>
              <h2 className="text-2xl font-semibold mb-2">AI Video Clipper</h2>
              <p className="max-w-md text-sm">
                Upload a video or paste a YouTube link to automatically extract viral clips
                with dynamic captions — 100% free, runs locally.
              </p>
            </div>
          )}
        </section>
      </main>
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}