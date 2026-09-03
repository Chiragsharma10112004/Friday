"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  LayoutDashboard,
  MessageSquareCode,
  CheckSquare,
  Code2,
  Activity,
  FolderGit2,
  BrainCircuit,
  Briefcase,
  Sparkles,
  BarChart3,
  History,
  Settings,
  Terminal,
  Play,
  Zap,
} from "lucide-react";
import { Modal } from "@/components/ui/Modal";

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

const COMMAND_ITEMS = [
  { id: "home", title: "Go to Command Center", category: "Navigation", icon: LayoutDashboard, href: "/" },
  { id: "chat", title: "Open AI Chat", category: "Navigation", icon: MessageSquareCode, href: "/chat" },
  { id: "tasks", title: "View Tasks & Workflows", category: "Navigation", icon: CheckSquare, href: "/tasks" },
  { id: "dev", title: "Developer Mode & AST Inspector", category: "Navigation", icon: Code2, href: "/developer" },
  { id: "health", title: "Self-Healing & Diagnostics", category: "Navigation", icon: Activity, href: "/health" },
  { id: "projects", title: "Projects & Repositories", category: "Navigation", icon: FolderGit2, href: "/projects" },
  { id: "memory", title: "Long-Term Memory Facts", category: "Navigation", icon: BrainCircuit, href: "/memory" },
  { id: "jobs", title: "Job Discovery Search", category: "Navigation", icon: Search, href: "/jobs" },
  { id: "apps", title: "Applications Pipeline", category: "Navigation", icon: Briefcase, href: "/applications" },
  { id: "intel", title: "Career Intelligence & Briefings", category: "Navigation", icon: Sparkles, href: "/intelligence" },
  { id: "analytics", title: "Conversion Funnel & Analytics", category: "Navigation", icon: BarChart3, href: "/analytics" },
  { id: "activity", title: "System Audit Activity", category: "Navigation", icon: History, href: "/activity" },
  { id: "settings", title: "Settings & Invariant Rules", category: "Navigation", icon: Settings, href: "/settings" },
];

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  const filteredItems = COMMAND_ITEMS.filter((item) =>
    item.title.toLowerCase().includes(search.toLowerCase()) ||
    item.category.toLowerCase().includes(search.toLowerCase())
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        isOpen ? onClose() : null;
      }
      if (!isOpen) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % (filteredItems.length || 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % (filteredItems.length || 1));
      } else if (e.key === "Enter" && filteredItems[selectedIndex]) {
        e.preventDefault();
        handleSelect(filteredItems[selectedIndex]);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, selectedIndex, filteredItems]);

  const handleSelect = (item: (typeof COMMAND_ITEMS)[0]) => {
    onClose();
    if (item.href) {
      router.push(item.href);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="FRIDAY Command Core" description="Quick jump and action dispatcher" maxWidth="lg">
      <div className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Type a command or screen name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 font-sans"
            autoFocus
          />
        </div>

        <div className="max-h-72 overflow-y-auto space-y-1 pr-1">
          {filteredItems.length === 0 ? (
            <p className="text-center py-6 text-xs text-slate-500">No commands found matching "{search}"</p>
          ) : (
            filteredItems.map((item, index) => {
              const Icon = item.icon;
              const isSelected = index === selectedIndex;
              return (
                <button
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-left text-xs transition ${
                    isSelected
                      ? "bg-cyan-950/80 text-cyan-200 border border-cyan-800/60 shadow-sm"
                      : "text-slate-300 hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isSelected ? "text-cyan-400" : "text-slate-400"}`} />
                    <span className="font-medium">{item.title}</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 px-2 py-0.5 rounded bg-slate-800/40">
                    {item.category}
                  </span>
                </button>
              );
            })
          )}
        </div>

        <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500 font-mono">
          <span>Navigate with &uarr; &darr;</span>
          <span>Select with Enter</span>
          <span>Close with Esc</span>
        </div>
      </div>
    </Modal>
  );
};
