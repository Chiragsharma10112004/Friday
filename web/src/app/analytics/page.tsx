"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  TrendingUp,
  Layers,
  AlertOctagon,
  CheckCircle2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingSkeleton";
import { feedbackApi } from "@/lib/api";
import {
  AnalyticsSummaryResponse,
  ConversionFunnelResponse,
  PlatformPerformanceResponse,
  FieldIssueResponse,
} from "@/types";

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummaryResponse | null>(null);
  const [funnel, setFunnel] = useState<ConversionFunnelResponse | null>(null);
  const [platforms, setPlatforms] = useState<PlatformPerformanceResponse[]>([]);
  const [fieldIssues, setFieldIssues] = useState<FieldIssueResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [sumRes, funRes, platRes, issRes] = await Promise.allSettled([
        feedbackApi.getAnalyticsSummary(),
        feedbackApi.getFunnel(),
        feedbackApi.getPlatformMetrics(),
        feedbackApi.listFieldIssues({ resolved: false }),
      ]);

      if (sumRes.status === "fulfilled") setSummary(sumRes.value);
      if (funRes.status === "fulfilled") setFunnel(funRes.value);
      if (platRes.status === "fulfilled") setPlatforms(platRes.value);
      if (issRes.status === "fulfilled") setFieldIssues(issRes.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleResolveIssue = async (id: number) => {
    try {
      await feedbackApi.resolveFieldIssue(id);
      fetchData();
    } catch (err) {
      console.error("Failed to resolve field issue:", err);
    }
  };

  if (loading) return <LoadingState message="Aggregating Feedback Signals & Conversion Metrics..." />;

  const funnelSteps = [
    { label: "Discovered", value: funnel?.discovered || 0, color: "bg-slate-700" },
    { label: "Applied", value: funnel?.applied || 0, color: "bg-cyan-600" },
    { label: "Screening", value: funnel?.screen || 0, color: "bg-cyan-500" },
    { label: "Technical", value: funnel?.technical || 0, color: "bg-purple-500" },
    { label: "Final Round", value: funnel?.final_round || 0, color: "bg-amber-500" },
    { label: "Offers", value: funnel?.offers || 0, color: "bg-emerald-500" },
  ];

  const maxFunnelVal = Math.max(...funnelSteps.map((s) => s.value), 1);

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 font-sans flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            Outcome Feedback & Conversion Analytics
          </h2>
          <p className="text-xs text-slate-400">
            Conversion funnel analysis, ATS platform yield, and form-field failure diagnostics.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </Button>
      </div>

      <Card glow="cyan">
        <CardHeader>
          <div>
            <CardTitle>
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              Full-Stage Application Conversion Funnel
            </CardTitle>
            <CardDescription>
              Progression from discovery to offer across all active opportunities.
            </CardDescription>
          </div>
          <Badge variant="emerald" size="md">
            {summary?.overall_conversion_rate
              ? `${(summary.overall_conversion_rate * 100).toFixed(1)}% Conversion`
              : "Active Tracking"}
          </Badge>
        </CardHeader>

        <div className="space-y-4 pt-2">
          {funnelSteps.map((step) => {
            const percentage = Math.round((step.value / maxFunnelVal) * 100);
            return (
              <div key={step.label} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-semibold text-slate-200">{step.label}</span>
                  <span className="text-slate-400">{step.value} applications</span>
                </div>
                <div className="w-full h-3 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${step.color}`}
                    style={{ width: `${Math.max(percentage, 2)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="space-y-4">
          <CardHeader>
            <div>
              <CardTitle>
                <Layers className="w-4 h-4 text-purple-400" />
                ATS Platform Yield Breakdown
              </CardTitle>
              <CardDescription>Screening & offer pass-rates per job portal.</CardDescription>
            </div>
          </CardHeader>

          {platforms.length === 0 ? (
            <p className="text-xs text-slate-500 font-mono text-center py-4">No platform metrics recorded yet.</p>
          ) : (
            <div className="space-y-3">
              {platforms.map((plat) => (
                <div
                  key={plat.platform}
                  className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5 font-mono text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200 uppercase">{plat.platform}</span>
                    <Badge variant="cyan">{plat.total_applications} Apps</Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-[11px] text-slate-400 pt-1">
                    <div>Screen: <strong className="text-cyan-400">{Math.round(plat.screen_rate * 100)}%</strong></div>
                    <div>Offer: <strong className="text-emerald-400">{Math.round(plat.offer_rate * 100)}%</strong></div>
                    <div>Field Issues: <strong className="text-rose-400">{plat.field_issue_count}</strong></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="space-y-4">
          <CardHeader>
            <div>
              <CardTitle>
                <AlertOctagon className="w-4 h-4 text-rose-400" />
                ATS Form-Field Issue Diagnostics
              </CardTitle>
              <CardDescription>Unrecognized or failing ATS form selectors.</CardDescription>
            </div>
          </CardHeader>

          {fieldIssues.length === 0 ? (
            <div className="p-6 rounded-xl bg-slate-950/60 border border-slate-800 text-center text-xs text-emerald-400 font-mono">
              <CheckCircle2 className="w-5 h-5 mx-auto mb-2 text-emerald-400" />
              Zero unresolved ATS field issues!
            </div>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {fieldIssues.map((issue) => (
                <div
                  key={issue.id}
                  className="p-3 rounded-xl bg-slate-950 border border-rose-900/40 flex items-center justify-between gap-3 text-xs font-mono"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Badge variant="rose">{issue.platform}</Badge>
                      <span className="font-semibold text-slate-200">{issue.field_name}</span>
                    </div>
                    <p className="text-[10px] text-slate-400 font-sans">{issue.error_message || issue.issue_type}</p>
                  </div>

                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleResolveIssue(issue.id)}
                  >
                    Resolve
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
