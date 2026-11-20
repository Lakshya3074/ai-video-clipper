"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { UploadArea } from "@/components/UploadArea";
import { JobProgress } from "@/components/JobProgress";
import { ClipStudio } from "@/components/ClipStudio";
import { Header } from "@/components/Header";
import { Toast } from "@/components/Toast";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type JobStatus = "idle" | "uploading" | "processing" | "analyzing" | "rendering" | "completed" | "error";

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
  status: JobStatus;
  progress: number;
  currentStep: string;
  detail?: string;
  clips: ViralClip[];
  error?: string;
}

export default function Home() {
  const [job, setJob] = useState<JobData | null>(null);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const showToast = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  }, []);

  const connectWebSocket = useCallback((jobId: string) => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    const ws = new WebSocket(`${API_BASE.replace("http", "ws")}/jobs/${jobId}/ws`);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setJob((prev) => prev ? { ...prev, ...data } : data);
      } catch (e) {
        console.error("WS parse error", e);
      }
    };
    ws.onerror = () => {
      console.log("WS error, falling back to polling");
      startPolling(jobId);
    };
    ws.onclose = () => {
      console.log("WS closed");
    };
    wsRef.current = ws;
  }, []);

  const startPolling = useCallback((jobId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/jobs/${jobId}/progress`);
        if (res.ok) {
          const data = await res.json();
          setJob((prev) => prev ? { ...prev, ...data } : data);
          if (data.status === "completed" || data.status === "failed") {
            if (pollingRef.current) clearInterval(pollingRef.current);
          }
        }
      } catch (e) {
        console.error("Polling error", e);
      }
    }, 1000);
  }, []);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    if (wsRef.current) wsRef.current.close();
  }, []);

  const handleUpload = async (file: File | null, url: string | null) => {
    const formData = new FormData();
    formData.append("source_type", file ? "upload" : "url");
    if (file) formData.append("file", file);
    if (url) formData.append("url", url);

    try {
      const res = await fetch(`${API_BASE}/jobs`, { method: "POST", body: formData });
      if (!res.ok) throw new Error("Failed to create job");
      const data = await res.json();
      setJob({ jobId: data.job_id, status: "processing", progress: 0, currentStep: "Queued", clips: [] });
      connectWebSocket(data.job_id);
      showToast("Job started! Processing video...", "success");
    } catch (e) {
      showToast("Failed to start job: " + (e as Error).message, "error");
    }
  };

  const handleRender = async (clips: ViralClip[]) => {
    if (!job) return;
    try {
      const res = await fetch(`${API_BASE}/jobs/${job.jobId}/render`, {
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

  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <main className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        <aside className="w-full lg:w-96 border-r border-border bg-card flex flex-col">
          <UploadArea onUpload={handleUpload} disabled={!!job} />
          <JobProgress job={job} />
        </aside>
        <section className="flex-1 overflow-auto p-4 lg:p-6">
          {job && job.clips.length > 0 && (
            <ClipStudio
              jobId={job.jobId}
              clips={job.clips}
              status={job.status}
              onRender={handleRender}
            />
          )}
          {!job && (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
              <div className="text-6xl mb-4">🎬</div>
              <h2 className="text-2xl font-semibold mb-2">AI Video Clipper</h2>
              <p className="max-w-md">
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