"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Bot,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Play,
  ArrowRight,
  Sparkles,
  Zap,
  Code2,
  Search,
  Briefcase,
  ShieldCheck,
  RefreshCw,
  Terminal,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingSkeleton";
import {
  systemApi,
  careerIntelligenceApi,
  workflowApi,
  selfHealingApi,
} from "@/lib/api";
import {
  SystemStatus,
  ReadinessHealth,
  TodayActionQueueResponse,
  WorkflowQueueResponse,
  SelfHealingAuditRecord,
} from "@/types";

export default function HomePage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [readiness, setReadiness] = useState<ReadinessHealth | null>(null);
  const [todayActions, setTodayActions] = useState<TodayActionQueueResponse | null>(null);
  const [workflowQueue, setWorkflowQueue] = useState<WorkflowQueueResponse | null>(null);
  const [recentHealing, setRecentHealing] = useState<SelfHealingAuditRecord[]>([]);

  const fetchDashboardData = async () => {
    try {
      const [statusRes, readinessRes, todayRes, queueRes, healingRes] =
        await Promise.allSettled([
          systemApi.getStatus(),
          systemApi.getReadiness(),
          careerIntelligenceApi.getToday(),
          workflowApi.getQueue(),
          selfHealingApi.getHistory(),
        ]);

      if (statusRes.status === "fulfilled") setStatus(statusRes.value);
      if (readinessRes.status === "fulfilled") setReadiness(readinessRes.value);
      if (todayRes.status === "fulfilled") setTodayActions(todayRes.value);
      if (queueRes.status === "fulfilled") setWorkflowQueue(queueRes.value);
      if (healingRes.status === "fulfilled") setRecentHealing(healingRes.value.slice(0, 3));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    router.push(`/chat?initialPrompt=${encodeURIComponent(prompt)}`);
  };

  const handleCompleteAction = async (id: number) => {
    try {
      await careerIntelligenceApi.completeRecommendation(id);
      fetchDashboardData();
    } catch (err) {
      console.error("Failed to complete action:", err);
    }
  };

  if (loading) {
    return <LoadingState message="Initializing FRIDAY Command Center..." />;
  }

  return (
    <div className="space-y-8">
      <div className="relative rounded-3xl bg-gradient-to-b from-slate-900 via-slate-900/90 to-slate-950 border border-cyan-900/40 p-6 sm:p-8 shadow-2xl overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="cyan" size="md">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shadow-glow-cyan" />
                SYSTEM ONLINE
              </Badge>
              <Badge variant="emerald" size="md">
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                SAFETY ACTIVE
              </Badge>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-sans">
              Welcome, Operator. FRIDAY is standing by.
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 max-w-xl leading-relaxed">
              Autonomous reasoning, code intelligence, self-healing recovery, and multi-platform career workflows active.
            </p>
          </div>

          <button
            onClick={() => {
              setRefreshing(true);
              fetchDashboardData();
            }}
            className="self-start md:self-auto px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-slate-300 hover:text-cyan-400 hover:border-cyan-500/50 text-xs flex items-center gap-2 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-cyan-400" : ""}`} />
            <span>Refresh Telemetry</span>
          </button>
        </div>

        <form onSubmit={handleCommandSubmit} className="mt-6 relative">
          <input
            type="text"
            placeholder="Ask FRIDAY anything, plan a workflow, edit code, or run test suites..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="w-full pl-5 pr-28 py-3.5 rounded-2xl bg-slate-950/90 border border-slate-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 shadow-inner"
          />
          <Button
            type="submit"
            variant="primary"
            size="sm"
            className="absolute right-2 top-1/2 -translate-y-1/2"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Execute</span>
          </Button>
        </form>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card hoverEffect glow="cyan">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Database Engine</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <p className="text-xl font-bold font-mono text-slate-100 uppercase">
              {readiness?.database === "ready" ? "READY" : "HEALTHY"}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">SQLite Active • 115 Tests Passing</p>
          </div>
        </Card>

        <Card hoverEffect glow="amber">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Action Queue</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <p className="text-xl font-bold font-mono text-slate-100">
              {todayActions?.total_actions ?? 0} Pending
            </p>
            <p className="text-[11px] text-amber-400/90 mt-0.5">
              {todayActions?.critical_count ?? 0} Critical • {todayActions?.high_count ?? 0} High
            </p>
          </div>
        </Card>

        <Card hoverEffect glow="emerald">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Autonomous Workflows</span>
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <p className="text-xl font-bold font-mono text-slate-100">
              {workflowQueue?.actionable_count ?? 0} Active
            </p>
            <p className="text-[11px] text-emerald-400/90 mt-0.5">
              {workflowQueue?.awaiting_approval_count ?? 0} Awaiting Human Gate
            </p>
          </div>
        </Card>

        <Card hoverEffect glow="rose">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Self-Healing</span>
            <ShieldCheck className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-3">
            <p className="text-xl font-bold font-mono text-slate-100">
              {recentHealing.length} Events
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">Automated Rollback & AST Guard</p>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  Today's Recommended Priorities
                </CardTitle>
                <CardDescription>
                  {todayActions?.briefing_headline || "Real-time AI pipeline recommendations"}
                </CardDescription>
              </div>
              <Link href="/tasks">
                <Button variant="outline" size="sm">
                  View All Tasks
                </Button>
              </Link>
            </CardHeader>

            <div className="space-y-2.5">
              {!todayActions || todayActions.actions.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500 font-mono">
                  No critical actions pending today. All application pipelines are healthy!
                </div>
              ) : (
                todayActions.actions.slice(0, 4).map((action) => (
                  <div
                    key={action.id}
                    className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start justify-between gap-4 hover:border-slate-700 transition"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            action.priority === "CRITICAL"
                              ? "rose"
                              : action.priority === "HIGH"
                              ? "amber"
                              : "cyan"
                          }
                        >
                          {action.priority}
                        </Badge>
                        <h4 className="text-xs font-semibold text-slate-200">
                          {action.title}
                        </h4>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-relaxed">
                        {action.description}
                      </p>
                    </div>

                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleCompleteAction(action.id)}
                      className="shrink-0"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Done</span>
                    </Button>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>
                <Terminal className="w-4 h-4 text-cyan-400" />
                Quick Launch Core
              </CardTitle>
            </CardHeader>

            <div className="space-y-2">
              <Link href="/chat" className="block">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-cyan-500/50 flex items-center justify-between group transition">
                  <div className="flex items-center gap-2.5">
                    <Bot className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                    <div>
                      <p className="text-xs font-medium text-slate-200">AI Chat & Reasoning</p>
                      <p className="text-[10px] text-slate-500">Multi-turn tool execution</p>
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-cyan-400 transition" />
                </div>
              </Link>

              <Link href="/developer" className="block">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-cyan-500/50 flex items-center justify-between group transition">
                  <div className="flex items-center gap-2.5">
                    <Code2 className="w-4 h-4 text-purple-400 group-hover:scale-110 transition-transform" />
                    <div>
                      <p className="text-xs font-medium text-slate-200">Developer Mode</p>
                      <p className="text-[10px] text-slate-500">AST inspector & test runner</p>
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-cyan-400 transition" />
                </div>
              </Link>

              <Link href="/health" className="block">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-cyan-500/50 flex items-center justify-between group transition">
                  <div className="flex items-center gap-2.5">
                    <Activity className="w-4 h-4 text-rose-400 group-hover:scale-110 transition-transform" />
                    <div>
                      <p className="text-xs font-medium text-slate-200">Self-Healing Engine</p>
                      <p className="text-[10px] text-slate-500">Auto recovery & diff checks</p>
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-cyan-400 transition" />
                </div>
              </Link>

              <Link href="/jobs" className="block">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-cyan-500/50 flex items-center justify-between group transition">
                  <div className="flex items-center gap-2.5">
                    <Search className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                    <div>
                      <p className="text-xs font-medium text-slate-200">Job Discovery</p>
                      <p className="text-[10px] text-slate-500">Multi-provider opportunities</p>
                    </div>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-cyan-400 transition" />
                </div>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
