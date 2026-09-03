"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Play,
  Terminal,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DiffViewer } from "@/components/ui/DiffViewer";
import { LoadingState } from "@/components/ui/LoadingSkeleton";
import { selfHealingApi, systemApi } from "@/lib/api";
import {
  SelfHealingAuditRecord,
  ReadinessHealth,
  DiagnosticReport,
  RemediationProposal,
  RemediationResult,
} from "@/types";
import { formatDate } from "@/lib/utils";

export default function HealthPage() {
  const [history, setHistory] = useState<SelfHealingAuditRecord[]>([]);
  const [readiness, setReadiness] = useState<ReadinessHealth | null>(null);
  const [loading, setLoading] = useState(true);

  const [errorMessage, setErrorMessage] = useState("SyntaxError: invalid syntax in worker.py");
  const [tracebackText, setTracebackText] = useState(
    'File "worker.py", line 14\n    def process_task(\nSyntaxError: invalid syntax'
  );
  const [diagnosing, setDiagnosing] = useState(false);
  const [diagnosticReport, setDiagnosticReport] = useState<DiagnosticReport | null>(null);
  const [proposal, setProposal] = useState<RemediationProposal | null>(null);
  const [autoHealResult, setAutoHealResult] = useState<RemediationResult | null>(null);

  const fetchData = async () => {
    try {
      const [histRes, readRes] = await Promise.allSettled([
        selfHealingApi.getHistory(),
        systemApi.getReadiness(),
      ]);

      if (histRes.status === "fulfilled") setHistory(histRes.value);
      if (readRes.status === "fulfilled") setReadiness(readRes.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSimulateDiagnosis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!errorMessage.trim() || !tracebackText.trim()) return;
    setDiagnosing(true);
    setDiagnosticReport(null);
    setProposal(null);
    setAutoHealResult(null);

    try {
      const report = await selfHealingApi.diagnose(errorMessage, tracebackText);
      setDiagnosticReport(report);

      const prop = await selfHealingApi.plan(report);
      setProposal(prop);
    } catch (err) {
      console.error("Diagnosis simulation failed:", err);
    } finally {
      setDiagnosing(false);
    }
  };

  const handleAutoHeal = async () => {
    setDiagnosing(true);
    try {
      const res = await selfHealingApi.autoHeal({
        errorMessage,
        tracebackText,
        approved: true,
      });
      setAutoHealResult(res);
      fetchData();
    } catch (err: any) {
      console.error("Auto heal execution failed:", err);
      setAutoHealResult({
        proposal_id: "auto-error",
        status: "VALIDATION_FAILED",
        strategy_applied: "AST_FUNCTION_REPLACE",
        target_file: "worker.py",
        validation_passed: false,
        attempts: 1,
        error: err?.message || "Remediation failed",
      });
    } finally {
      setDiagnosing(false);
    }
  };

  if (loading) return <LoadingState message="Connecting to Self-Healing Diagnostics Core..." />;

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 font-sans flex items-center gap-2">
            <Activity className="w-5 h-5 text-rose-400" />
            Self-Healing & Diagnostics Engine
          </h2>
          <p className="text-xs text-slate-400">
            Real-time error classification, AST remediation planning, bounded retry, and automated rollback.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Telemetry</span>
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card hoverEffect glow="emerald">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Database Engine</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-xl font-bold font-mono text-slate-100 mt-2 uppercase">
            {readiness?.database || "READY"}
          </p>
          <p className="text-[11px] text-emerald-400/90 mt-0.5">SQLite Active • Thread Confined</p>
        </Card>

        <Card hoverEffect glow="cyan">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Classification Tiers</span>
            <Sparkles className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-xl font-bold font-mono text-slate-100 mt-2">8 Categories</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Syntax, Import, Runtime, Config</p>
        </Card>

        <Card hoverEffect glow="rose">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Safety Guard</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-xl font-bold font-mono text-slate-100 mt-2">Auto-Rollback</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Pre-edit Snapshot Protection</p>
        </Card>
      </div>

      <Card glow="cyan">
        <CardHeader>
          <div>
            <CardTitle>
              <Terminal className="w-4 h-4 text-cyan-400" />
              Interactive Diagnostic & Remediation Simulator
            </CardTitle>
            <CardDescription>
              Test FRIDAY's failure classification, remediation strategy formulation, and auto-heal pipeline.
            </CardDescription>
          </div>
        </CardHeader>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <form onSubmit={handleSimulateDiagnosis} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Error Message *</label>
              <input
                type="text"
                required
                value={errorMessage}
                onChange={(e) => setErrorMessage(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Traceback / Stack Trace *</label>
              <textarea
                rows={5}
                required
                value={tracebackText}
                onChange={(e) => setTracebackText(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500 resize-none"
              />
            </div>

            <div className="flex gap-3">
              <Button type="submit" variant="secondary" size="sm" isLoading={diagnosing}>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Classify & Plan</span>
              </Button>
              <Button type="button" variant="primary" size="sm" onClick={handleAutoHeal} isLoading={diagnosing}>
                <Play className="w-3.5 h-3.5" />
                <span>Execute Auto-Heal</span>
              </Button>
            </div>
          </form>

          <div className="space-y-4">
            {diagnosticReport ? (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200">Diagnostic Classification:</span>
                  <Badge variant="rose">{diagnosticReport.category}</Badge>
                </div>
                <div className="text-[11px] font-mono space-y-1 text-slate-400">
                  <p>Target File: <span className="text-cyan-400">{diagnosticReport.target_file || "Detected from stack"}</span></p>
                  <p>Line: <span className="text-cyan-400">{diagnosticReport.target_line || "N/A"}</span></p>
                  <p>Strategy: <span className="text-emerald-400">{proposal?.strategy || "AST_REPAIR"}</span></p>
                  <p>Risk Tier: <span className="text-amber-400">{proposal?.risk_level || "LOW"}</span></p>
                </div>
              </div>
            ) : null}

            {proposal?.diff_preview ? (
              <div>
                <span className="text-xs font-semibold text-slate-300 block mb-1">Proposed AST Diff:</span>
                <DiffViewer diffText={proposal.diff_preview} />
              </div>
            ) : null}

            {autoHealResult ? (
              <div className={`p-4 rounded-xl border ${autoHealResult.validation_passed ? "bg-emerald-950/40 border-emerald-800/60" : "bg-rose-950/40 border-rose-800/60"} space-y-2`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200">Auto-Heal Result:</span>
                  <Badge variant={autoHealResult.validation_passed ? "emerald" : "rose"}>
                    {autoHealResult.status}
                  </Badge>
                </div>
                <p className="text-xs text-slate-300 font-mono">
                  Strategy: {autoHealResult.strategy_applied} • Attempts: {autoHealResult.attempts}
                </p>
                {autoHealResult.diff_applied ? (
                  <DiffViewer diffText={autoHealResult.diff_applied} />
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>
              <RotateCcw className="w-4 h-4 text-cyan-400" />
              Remediation & Rollback History
            </CardTitle>
            <CardDescription>
              Chronological ledger of autonomous AST repairs and snapshot rollbacks.
            </CardDescription>
          </div>
        </CardHeader>

        {history.length === 0 ? (
          <p className="text-xs text-slate-500 font-mono p-4 rounded-xl bg-slate-950 border border-slate-800 text-center">
            No self-healing events recorded yet.
          </p>
        ) : (
          <div className="space-y-2">
            {history.map((record) => (
              <div
                key={record.id}
                className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between gap-4 text-xs font-mono"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={record.validation_passed ? "emerald" : "rose"}>
                      {record.category}
                    </Badge>
                    <span className="font-semibold text-slate-200">{record.target_file}</span>
                    <span className="text-slate-500">• {record.strategy}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans">{record.summary}</p>
                </div>

                <div className="text-right shrink-0">
                  <Badge variant={record.validation_passed ? "emerald" : "amber"}>
                    {record.status}
                  </Badge>
                  <p className="text-[10px] text-slate-500 mt-1">{formatDate(record.timestamp)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
