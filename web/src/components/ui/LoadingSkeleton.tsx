import React from "react";
import { cn } from "@/lib/utils";

export const Skeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div
    className={cn(
      "animate-pulse rounded-lg bg-slate-800/60 border border-slate-800/40",
      className
    )}
  />
);

export const LoadingState: React.FC<{ message?: string }> = ({
  message = "Loading FRIDAY telemetry...",
}) => (
  <div className="flex flex-col items-center justify-center p-12 text-center space-y-3">
    <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin shadow-glow-cyan" />
    <p className="text-xs font-mono text-cyan-400/80 tracking-wide">{message}</p>
  </div>
);
