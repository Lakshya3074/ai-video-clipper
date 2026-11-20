import { Sparkles, Zap, CheckCircle } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50 drag-region">
      <div className="max-w-full mx-auto px-4 lg:px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="relative">
              <Sparkles className="w-6 h-6 text-primary" />
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-primary rounded-full animate-pulse" />
            </div>
            <span className="font-bold text-xl tracking-tight">AI Video Clipper</span>
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-secondary rounded-full">
            <Zap className="w-3.5 h-3.5 text-yellow-400" />
            <span>100% Local</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-secondary rounded-full">
            <CheckCircle className="w-3.5 h-3.5 text-green-400" />
            <span>Free Forever</span>
          </div>
        </div>
      </div>
    </header>
  );
}