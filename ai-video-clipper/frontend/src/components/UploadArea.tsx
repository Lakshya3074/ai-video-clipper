"use client";

import { useState, useCallback, useRef, DragEvent, ChangeEvent } from "react";
import { Upload, FileVideo, Link, X, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadAreaProps {
  onUpload: (file: File | null, url: string | null) => void;
  disabled?: boolean;
}

export function UploadArea({ onUpload, disabled }: UploadAreaProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [showUrl, setShowUrl] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File) => {
    const validTypes = ["video/mp4", "video/quicktime", "video/x-matroska", "video/webm"];
    const maxSize = 2 * 1024 * 1024 * 1024; // 2GB

    if (!validTypes.includes(file.type)) {
      return "Please select a valid video file (MP4, MOV, MKV, WebM)";
    }
    if (file.size > maxSize) {
      return "File size must be less than 2GB";
    }
    return null;
  };

  const handleFileSelect = useCallback((file: File) => {
    const err = validateFile(file);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    onUpload(file, null);
  }, [onUpload]);

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleFileInputChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(file);
    e.target.value = "";
  }, [handleFileSelect]);

  const handleUrlSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    const url = urlInput.trim();
    if (!url) return;
    try {
      new URL(url);
      setError(null);
      onUpload(null, url);
    } catch {
      setError("Please enter a valid URL");
    }
  }, [urlInput, onUpload]);

  const triggerFileInput = () => fileInputRef.current?.click();

  if (disabled) {
    return (
      <div className="flex-1 flex flex-col p-6">
        <div className="text-center text-muted-foreground">
          <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-primary" />
          <p>Processing video...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col p-6 space-y-6">
      <div
        className={cn(
          "relative border-2 border-dashed rounded-xl p-8 text-center transition-all",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50"
        )}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={triggerFileInput}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/mp4,video/quicktime,video/x-matroska,video/webm"
          onChange={handleFileInputChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={disabled}
        />
        <FileVideo className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
        <p className="text-lg font-medium mb-1">
          {isDragActive ? "Drop video here" : "Click or drag video to upload"}
        </p>
        <p className="text-sm text-muted-foreground">
          MP4, MOV, MKV, WebM · Up to 2GB
        </p>
      </div>

      <div className="relative">
        <div className="flex items-center text-muted-foreground">
          <span className="flex-1 border-t" />
          <span className="px-4 text-xs uppercase tracking-wider">Or</span>
          <span className="flex-1 border-t" />
        </div>
      </div>

      <button
        type="button"
        onClick={() => setShowUrl(!showUrl)}
        className={cn(
          "w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors",
          showUrl
            ? "bg-primary text-primary-foreground"
            : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
        )}
        disabled={disabled}
      >
        <Link className="w-4 h-4" />
        <span>{showUrl ? "Switch to file upload" : "Paste YouTube / Video URL"}</span>
      </button>

      {showUrl && (
        <form onSubmit={handleUrlSubmit} className="space-y-3 animate-slide-down">
          <div className="relative">
            <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://youtube.com/watch?v=... or any video URL"
              className="w-full pl-10 pr-4 py-2.5 bg-input border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              disabled={disabled}
            />
          </div>
          <button
            type="submit"
            className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
            disabled={disabled}
          >
            Analyze Video
          </button>
        </form>
      )}

      {error && (
        <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm animate-slide-down">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-destructive/70 hover:text-destructive">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}