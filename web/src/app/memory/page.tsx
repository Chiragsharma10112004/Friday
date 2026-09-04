"use client";

import React, { useState, useEffect } from "react";
import {
  BrainCircuit,
  Plus,
  Trash2,
  RefreshCw,
  Search,
  Key,
  MessageSquare,
  Sparkles,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { LoadingState } from "@/components/ui/LoadingSkeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { memoryApi } from "@/lib/api";
import { MemoryResponse, ChatHistoryItem } from "@/types";

export default function MemoryPage() {
  const [memories, setMemories] = useState<Record<string, string>>({});
  const [history, setHistory] = useState<ChatHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [search, setSearch] = useState("");

  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("");
  const [saving, setSaving] = useState(false);

  const fetchData = async () => {
    try {
      const [memRes, histRes] = await Promise.allSettled([
        memoryApi.getAllMemory(),
        memoryApi.getChatHistory(30),
      ]);

      if (memRes.status === "fulfilled") setMemories(memRes.value.memories || {});
      if (histRes.status === "fulfilled") setHistory(histRes.value || []);
      if (memRes.status === "fulfilled" && memRes.value) {
        const val: any = memRes.value;
        setMemories(val.memories || (typeof val === "object" && !Array.isArray(val) ? val : {}));
      }
      if (histRes.status === "fulfilled" && histRes.value) {
        setHistory(Array.isArray(histRes.value) ? histRes.value : []);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSaveMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newValue.trim()) return;
    setSaving(true);
    try {
      await memoryApi.saveMemory(newKey.trim(), newValue.trim());
      setIsModalOpen(false);
      setNewKey("");
      setNewValue("");
      fetchData();
    } catch (err) {
      console.error("Failed to save memory:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteMemory = async (key: string) => {
    try {
      await memoryApi.deleteMemory(key);
      fetchData();
    } catch (err) {
      console.error("Failed to delete memory:", err);
    }
  };

  const filteredEntries = Object.entries(memories).filter(
    ([k, v]) =>
      k.toLowerCase().includes(search.toLowerCase()) ||
      v.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <LoadingState message="Retrieving long-term memory & context..." />;

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 font-sans flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-cyan-400" />
            Long-Term Memory & Context Core
          </h2>
          <p className="text-xs text-slate-400">
            Permanent user preferences, career facts, and multi-turn conversational history.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </Button>
          <Button variant="primary" size="sm" onClick={() => setIsModalOpen(true)}>
            <Plus className="w-4 h-4" />
            <span>Add Fact</span>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Filter memory facts..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <span className="text-xs font-mono text-slate-500">
              {filteredEntries.length} Stored Keys
            </span>
          </div>

          {filteredEntries.length === 0 ? (
            <EmptyState
              icon={BrainCircuit}
              title="No memory facts found"
              description="Store permanent user preferences, career skills, or system instructions."
              actionLabel="Add Memory Fact"
              onAction={() => setIsModalOpen(true)}
            />
          ) : (
            <div className="space-y-2.5">
              {filteredEntries.map(([key, value]) => (
                <Card key={key} className="p-3.5 flex items-start justify-between gap-4 hover:border-slate-700 transition">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Key className="w-3.5 h-3.5 text-cyan-400" />
                      <span className="font-mono text-xs font-semibold text-cyan-300">{key}</span>
                    </div>
                    <p className="text-xs text-slate-300 font-sans leading-relaxed">{value}</p>
                  </div>

                  <button
                    onClick={() => handleDeleteMemory(key)}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition shrink-0"
                    title="Delete Memory Fact"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </Card>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>
                  <MessageSquare className="w-4 h-4 text-purple-400" />
                  Conversation Context
                </CardTitle>
                <CardDescription>Recent conversation turns persisted in SQLite.</CardDescription>
              </div>
            </CardHeader>

            {history.length === 0 ? (
              <p className="text-xs text-slate-500 font-mono text-center py-4">No recent history.</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {history.map((item, index) => (
                  <div
                    key={index}
                    className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs space-y-1"
                  >
                    <span className="font-mono text-[10px] text-slate-500 uppercase">
                      {item.role === "user" ? "Operator" : "FRIDAY"}
                    </span>
                    <p className="text-slate-300 line-clamp-3">{item.content}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Store Permanent Fact"
        description="Add a key-value fact into FRIDAY's long-term contextual memory."
      >
        <form onSubmit={handleSaveMemory} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Key Name *</label>
            <input
              type="text"
              required
              placeholder="e.g. target_salary, preferred_tech_stack, timezone"
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Fact Value *</label>
            <textarea
              rows={3}
              required
              placeholder="e.g. Python, FastAPI, TypeScript, Next.js, remote US only"
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 resize-none font-sans"
            />
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <Button variant="outline" size="sm" type="button" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={saving}>
              Save Memory
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
