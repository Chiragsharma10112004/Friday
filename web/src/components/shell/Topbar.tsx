"use client";

import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Search, Command, ShieldCheck, Terminal, Cpu, RefreshCw } from "lucide-react";
import { systemApi } from "@/lib/api";
import { SystemStatus } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";

export interface TopbarProps {
  onOpenCommandPalette: () => void;
}

const ROUTE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/": { title: "Command Center", subtitle: "Real-time AI telemetry, priority queue & system status" },
  "/chat": { title: "AI Chat & Reasoning", subtitle: "Conversational intelligence with tool orchestration" },
  "/tasks": { title: "Tasks & Planning", subtitle: "Autonomous workflow queue, action steps & human approval gates" },
  "/developer": { title: "Developer Mode", subtitle: "AST workspace analyzer, symbol catalog & safe test runner" },
  "/health": { title: "Self-Healing & Telemetry", subtitle: "Diagnostic telemetry, automated recovery & rollback history" },
  "/projects": { title: "Projects & Codebases", subtitle: "Monitored repositories, file metrics & test coverage" },
  "/memory": { title: "Context & Memory", subtitle: "Extracted long-term user facts and conversational history" },
  "/jobs": { title: "Multi-Platform Discovery", subtitle: "Multi-provider job scraping, match scoring & pipeline converter" },
  "/applications": { title: "Application Pipeline", subtitle: "Full lifecycle tracking, interview rounds & follow-up scheduler" },
  "/intelligence": { title: "Career Intelligence", subtitle: "Daily briefings, application health audits & recommendation engine" },
  "/analytics": { title: "Feedback & Analytics", subtitle: "Conversion funnel, ATS issues & machine learning signals" },
  "/activity": { title: "Activity Timeline", subtitle: "Chronological audit log of autonomous operations & events" },
  "/settings": { title: "System Preferences", subtitle: "Operating parameters, API providers & safety invariant controls" },
};

export const Topbar: React.FC<TopbarProps> = ({ onOpenCommandPalette }) => {
  const pathname = usePathname();
  const currentPath: string = pathname ?? "/";
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const routeInfo =
    (currentPath in ROUTE_TITLES ? ROUTE_TITLES[currentPath] : undefined) ?? {
      title: "FRIDAY OS",
      subtitle: "Autonomous AI Operating System",
    };

  const checkStatus = async () => {
    setIsRefreshing(true);
    try {
      const res = await systemApi.getStatus();
      setStatus(res);
      setIsOnline(true);
    } catch {
      setIsOnline(false);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="pl-10 lg:pl-0">
        <h1 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
          {routeInfo.title}
        </h1>
        <p className="text-[11px] text-slate-400 hidden sm:block truncate max-w-md">
          {routeInfo.subtitle}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onOpenCommandPalette}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 text-xs transition group focus:outline-none focus:ring-1 focus:ring-cyan-500"
        >
          <Search className="w-3.5 h-3.5 text-slate-400 group-hover:text-cyan-400" />
          <span className="hidden md:inline">Command Palette</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] font-mono text-slate-400">
            <Command className="w-2.5 h-2.5" /> K
          </kbd>
        </button>

        <div className="flex items-center gap-2">
          {isOnline ? (
            <Badge variant="cyan" size="sm" className="hidden sm:inline-flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse shadow-glow-cyan" />
              <span>{status ? `${status.assistant} v${status.version}` : "API Connected"}</span>
            </Badge>
          ) : (
            <Badge variant="rose" size="sm" className="inline-flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
              <span>API Offline</span>
            </Badge>
          )}

          <button
            onClick={checkStatus}
            title="Refresh backend telemetry"
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", isRefreshing && "animate-spin text-cyan-400")} />
          </button>
        </div>
      </div>
    </header>
  );
};
