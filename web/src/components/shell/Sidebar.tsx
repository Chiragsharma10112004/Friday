"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquareCode,
  CheckSquare,
  Code2,
  Activity,
  FolderGit2,
  BrainCircuit,
  Search,
  Briefcase,
  Sparkles,
  BarChart3,
  History,
  Settings,
  Menu,
  X,
  Bot,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { name: "Command Center", href: "/", icon: LayoutDashboard },
  { name: "AI Chat", href: "/chat", icon: MessageSquareCode },
  { name: "Tasks & Planning", href: "/tasks", icon: CheckSquare },
  { name: "Developer Mode", href: "/developer", icon: Code2 },
  { name: "Self-Healing", href: "/health", icon: Activity },
  { name: "Projects", href: "/projects", icon: FolderGit2 },
  { name: "Memory", href: "/memory", icon: BrainCircuit },
  { name: "Job Discovery", href: "/jobs", icon: Search },
  { name: "Applications", href: "/applications", icon: Briefcase },
  { name: "Career AI", href: "/intelligence", icon: Sparkles },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Activity Timeline", href: "/activity", icon: History },
  { name: "Settings", href: "/settings", icon: Settings },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const currentPath: string = pathname ?? "/";
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  return (
    <>
      <div className="lg:hidden fixed top-3 left-3 z-50">
        <button
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="p-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-300 hover:text-cyan-400 focus:outline-none"
        >
          {isMobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {isMobileOpen ? (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm"
          onClick={() => setIsMobileOpen(false)}
        />
      ) : null}

      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-40 w-64 bg-slate-950/95 lg:bg-slate-950/80 backdrop-blur-xl border-r border-slate-800/80 flex flex-col transition-transform duration-300 ease-in-out",
          isMobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-3 group"
            onClick={() => setIsMobileOpen(false)}
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-cyan-400 flex items-center justify-center shadow-glow-cyan group-hover:scale-105 transition-transform">
              <Bot className="w-5 h-5 text-slate-950" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold tracking-wider text-base text-slate-100 font-mono">
                  FRIDAY
                </span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-semibold">
                  OS 10.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">Autonomous AI Core</p>
            </div>
          </Link>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/"
                ? currentPath === "/"
                : currentPath === item.href || currentPath.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsMobileOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-150 group",
                  isActive
                    ? "bg-cyan-950/60 text-cyan-300 border border-cyan-800/60 shadow-sm"
                    : "text-slate-400 hover:text-slate-100 hover:bg-slate-900/80"
                )}
              >
                <Icon
                  className={cn(
                    "w-4 h-4 transition-transform group-hover:scale-110",
                    isActive ? "text-cyan-400" : "text-slate-500 group-hover:text-slate-300"
                  )}
                />
                <span className="flex-1">{item.name}</span>
                {isActive ? (
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-glow-cyan" />
                ) : null}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-slate-800/80">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-glow-emerald" />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-slate-200 truncate">Core System</p>
              <p className="text-[10px] text-emerald-400/90 font-mono">115 Tests Verified</p>
            </div>
            <Zap className="w-4 h-4 text-cyan-400" />
          </div>
        </div>
      </aside>
    </>
  );
};
