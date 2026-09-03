import React from "react";
import { cn } from "@/lib/utils";

export interface DiffViewerProps {
  diffText?: string | null;
  className?: string;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ diffText, className }) => {
  if (!diffText) {
    return (
      <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 text-xs font-mono text-slate-500 text-center">
        No diff preview available
      </div>
    );
  }

  const lines = diffText.split("\n");

  return (
    <div
      className={cn(
        "rounded-xl bg-slate-950 border border-slate-800/90 overflow-x-auto text-xs font-mono p-4",
        className
      )}
    >
      {lines.map((line, index) => {
        let lineStyle = "text-slate-400";
        let bgStyle = "bg-transparent";

        if (line.startsWith("+") && !line.startsWith("+++")) {
          lineStyle = "text-emerald-400";
          bgStyle = "bg-emerald-950/40";
        } else if (line.startsWith("-") && !line.startsWith("---")) {
          lineStyle = "text-rose-400";
          bgStyle = "bg-rose-950/40";
        } else if (line.startsWith("@@")) {
          lineStyle = "text-cyan-400 font-semibold";
          bgStyle = "bg-cyan-950/30";
        }

        return (
          <div
            key={index}
            className={cn("px-2 py-0.5 whitespace-pre rounded flex", bgStyle)}
          >
            <span className="w-8 select-none text-slate-600 text-right pr-3 inline-block">
              {index + 1}
            </span>
            <span className={cn("flex-1", lineStyle)}>{line}</span>
          </div>
        );
      })}
    </div>
  );
};
