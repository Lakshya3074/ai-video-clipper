"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { cn, formatTime, getViralityColor, getViralityBg } from "@/lib/utils";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize2,
  Minimize2,
  Scissors,
  Edit3,
  Trash2,
  Download,
  Star,
  Zap,
  Loader2,
  Check,
  X,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

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

interface ClipStudioProps {
  jobId: string;
  clips: ViralClip[];
  status: string;
  onRender: (clips: ViralClip[]) => void;
}

export function ClipStudio({ jobId, clips: initialClips, status, onRender }: ClipStudioProps) {
  const [clips, setClips] = useState<ViralClip[]>(initialClips);
  const [activeClipIndex, setActiveClipIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showTranscriptEditor, setShowTranscriptEditor] = useState(false);
  const [editedTranscript, setEditedTranscript] = useState("");
  const [rendering, setRendering] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const progressInterval = useRef<NodeJS.Timeout | null>(null);

  const activeClip = clips[activeClipIndex];

  useEffect(() => {
    setClips(initialClips);
    setActiveClipIndex(0);
  }, [initialClips]);

  const playPause = () => {
    if (!videoRef.current) return;
    if (isPlaying) videoRef.current.pause();
    else videoRef.current.play();
  };

  const handleTimeUpdate = () => {
    const video = videoRef.current;
    if (!video || !activeClip) return;
    if (video.currentTime >= activeClip.duration) {
      video.pause();
      setIsPlaying(false);
      video.currentTime = 0;
    }
  };

  const handleSeek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, Math.min(time, activeClip?.duration || 0));
    }
  };

  const updateClipTime = (field: "start_time" | "end_time", value: number) => {
    setClips((prev) =>
      prev.map((c, i) =>
        i === activeClipIndex
          ? { ...c, [field]: value, duration: field === "start_time" ? c.end_time - value : value - c.start_time }
          : c
      )
    );
  };

  const handleRender = async () => {
    setRendering(true);
    try {
      await onRender(clips);
    } finally {
      setRendering(false);
    }
  };

  const getClipVideoUrl = (clipId: string) => `${API_BASE}/jobs/${jobId}/clips/${clipId}/preview`;

  const formatTimeInput = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}.${ms.toString().padStart(2, "0")}`;
  };

  const parseTimeInput = (value: string): number => {
    const parts = value.split(":").map(Number);
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    if (parts.length === 3) return parts[0] * 60 + parts[1] + parts[2] / 100;
    return Number(value) || 0;
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 flex flex-col lg:flex-row gap-6 min-h-0">
        <div className="flex-1 lg:w-2/3 flex flex-col min-h-0">
          <div className="relative bg-black rounded-xl overflow-hidden flex-1 flex flex-col min-h-0">
            <video
              ref={videoRef}
              src={activeClip ? getClipVideoUrl(activeClip.id) : ""}
              className="w-full h-full object-contain"
              onTimeUpdate={handleTimeUpdate}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onEnded={() => setIsPlaying(false)}
              playsInline
            />

            <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/90 to-transparent">
              <div className="flex items-center gap-4 mb-2">
                <button
                  onClick={playPause}
                  className="p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
                  aria-label={isPlaying ? "Pause" : "Play"}
                >
                  {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                </button>

                <div className="flex-1 h-1.5 bg-white/20 rounded-full cursor-pointer relative" onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const pct = (e.clientX - rect.left) / rect.width;
                  handleSeek(pct * (activeClip?.duration || 0));
                }}>
                  <div
                    className="h-full bg-primary rounded-full transition-all duration-75"
                    style={{ width: `${activeClip && videoRef.current ? (videoRef.current.currentTime / activeClip.duration) * 100 : 0}%` }}
                  />
                </div>

                <span className="text-sm font-mono text-white/80 w-20 text-right">
                  {videoRef.current ? formatTime(videoRef.current.currentTime) : "0:00"} / {activeClip ? formatTime(activeClip.duration) : "0:00"}
                </span>

                <button
                  onClick={() => { if (videoRef.current) videoRef.current.volume = volume === 0 ? 1 : 0; setVolume(v => v === 0 ? 1 : 0); }}
                  className="p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
                >
                  {volume === 0 ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                </button>

                <button
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  className="p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
                >
                  {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {isFullscreen && (
              <div className="absolute top-4 right-4 z-10">
                <button
                  onClick={() => setIsFullscreen(false)}
                  className="p-2 rounded-full bg-black/50 hover:bg-black/70 text-white transition-colors"
                >
                  <Minimize2 className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>

          <div className="mt-4 grid grid-cols-3 gap-3">
            <div className="bg-card border border-border rounded-lg p-4">
              <label className="text-xs text-muted-foreground block mb-1">Start Time</label>
              <input
                type="text"
                value={formatTimeInput(activeClip?.start_time || 0)}
                onChange={(e) => updateClipTime("start_time", parseTimeInput(e.target.value))}
                className="w-full bg-background border border-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="bg-card border border-border rounded-lg p-4">
              <label className="text-xs text-muted-foreground block mb-1">End Time</label>
              <input
                type="text"
                value={formatTimeInput(activeClip?.end_time || 0)}
                onChange={(e) => updateClipTime("end_time", parseTimeInput(e.target.value))}
                className="w-full bg-background border border-border rounded px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="bg-card border border-border rounded-lg p-4">
              <label className="text-xs text-muted-foreground block mb-1">Duration</label>
              <div className="font-mono text-lg font-semibold">{activeClip ? formatDuration(activeClip.duration) : "0s"}</div>
            </div>
          </div>
        </div>

        <div className="lg:w-1/3 flex flex-col gap-4 min-w-0">
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-start justify-between gap-2 mb-3">
              <h3 className="font-semibold text-lg truncate pr-2">{activeClip?.title || "No clip selected"}</h3>
              <div className={cn("px-2 py-1 rounded-full text-xs font-medium flex-shrink-0", getViralityBg(activeClip?.virality_score || 0))}>
                <span className={cn(getViralityColor(activeClip?.virality_score || 0))}>
                  {activeClip?.virality_score || 0}/100
                </span>
              </div>
            </div>

            <p className="text-sm text-muted-foreground mb-4 line-clamp-3">{activeClip?.hook_reasoning || ""}</p>

            <div className="space-y-2">
              <label className="text-xs text-muted-foreground block mb-1">Transcript (editable)</label>
              <textarea
                value={editedTranscript || activeClip?.transcript || ""}
                onChange={(e) => setEditedTranscript(e.target.value)}
                onBlur={() => {
                  if (editedTranscript !== activeClip?.transcript) {
                    setClips(prev => prev.map((c, i) => i === activeClipIndex ? { ...c, transcript: editedTranscript } : c));
                  }
                }}
                className="w-full bg-background border border-border rounded-lg p-3 text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-primary min-h-[120px]"
                rows={5}
              />
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 flex-1 overflow-auto">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">All Clips</h3>
              <button
                onClick={handleRender}
                disabled={rendering || status === "rendering"}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {rendering ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                {rendering ? "Rendering..." : "Export All"}
              </button>
            </div>

            <div className="space-y-2">
              {clips.map((clip, index) => (
                <button
                  key={clip.id}
                  onClick={() => {
                    setActiveClipIndex(index);
                    setEditedTranscript(clip.transcript);
                    if (videoRef.current) {
                      videoRef.current.pause();
                      videoRef.current.currentTime = 0;
                    }
                  }}
                  className={cn(
                    "w-full text-left p-3 rounded-lg border transition-all flex items-start gap-3",
                    index === activeClipIndex
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/50"
                  )}
                >
                  <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-medium">{index + 1}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{clip.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatTime(clip.start_time)} - {formatTime(clip.end_time)} · {formatDuration(clip.duration)}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <Star className={cn("w-3 h-3", getViralityColor(clip.virality_score))} />
                      <span className={cn("text-xs font-medium", getViralityColor(clip.virality_score))}>
                        {clip.virality_score}/100
                      </span>
                    </div>
                  </div>
                  {index === activeClipIndex && (
                    <Check className="w-5 h-5 text-primary flex-shrink-0" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}