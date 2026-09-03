"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Activity,
  HeartPulse,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Clock,
  Briefcase,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingSkeleton";
import { careerIntelligenceApi } from "@/lib/api";
import {
  DashboardIntelligenceResponse,
  DailyBriefingResponse,
  ApplicationHealthItem,
} from "@/types";

export default function IntelligencePage() {
  const [dashboard, setDashboard] = useState<DashboardIntelligenceResponse | null>(null);
  const [briefing, setBriefing] = useState<DailyBriefingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshingRecs, setRefreshingRecs] = useState(false);

  const fetchData = async () => {
    try {
      const [dashRes, briefRes] = await Promise.allSettled([
        careerIntelligenceApi.getDashboard(),
        careerIntelligenceApi.getDailyBriefing(),
      ]);

      if (dashRes.status === "fulfilled") setDashboard(dashRes.value);
      if (briefRes.status === "fulfilled") setBriefing(briefRes.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRecalculate = async () => {
    setRefreshingRecs(true);
    try {
      await careerIntelligenceApi.refreshRecommendations();
      await fetchData();
    } catch (err) {
      console.error("Recalculation failed:", err);
    } finally {
      setRefreshingRecs(false);
    }
  };

  if (loading) return <LoadingState message="Synthesizing Career Intelligence & Health Audits..." />;

  const healthItems = dashboard?.pipeline_health?.items || [];

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 font-sans flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-400" />
            Career Intelligence & Health Auditing
          </h2>
          <p className="text-xs text-slate-400">
            Daily briefings, staleness audits, conversion bottlenecks, and proactive AI recommendations.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={handleRecalculate}
          isLoading={refreshingRecs}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Recalculate Recommendations</span>
        </Button>
      </div>

      <Card glow="amber">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-2xl bg-amber-950/80 border border-amber-800/60 text-amber-400 shrink-0">
            <Sparkles className="w-6 h-6" />
          </div>
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-2">
              <Badge variant="amber" size="md">DAILY BRIEFING</Badge>
              <span className="text-[11px] font-mono text-slate-400">
                {briefing?.generated_at ? new Date(briefing.generated_at).toLocaleDateString() : "Today"}
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-100 font-sans">
              {briefing?.headline || "Application Health & Action Queue Optimized"}
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">
              {dashboard?.briefing_snippet || "FRIDAY is actively monitoring your application pipeline for staleness and interview preparation milestones."}
            </p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card hoverEffect glow="emerald">
          <span className="text-xs font-medium text-slate-400">Healthy Pipelines</span>
          <p className="text-2xl font-bold font-mono text-slate-100 mt-2">
            {dashboard?.pipeline_health?.healthy_count ?? 0}
          </p>
          <p className="text-[11px] text-emerald-400/90 mt-0.5">Active & progressing</p>
        </Card>

        <Card hoverEffect glow="amber">
          <span className="text-xs font-medium text-slate-400">Attention Needed</span>
          <p className="text-2xl font-bold font-mono text-amber-400 mt-2">
            {dashboard?.pipeline_health?.attention_needed_count ?? 0}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">Follow-ups due</p>
        </Card>

        <Card hoverEffect glow="rose">
          <span className="text-xs font-medium text-slate-400">Stale Applications</span>
          <p className="text-2xl font-bold font-mono text-rose-400 mt-2">
            {dashboard?.pipeline_health?.stale_count ?? 0}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">&gt; 14 days without activity</p>
        </Card>

        <Card hoverEffect glow="rose">
          <span className="text-xs font-medium text-slate-400">Critical Issues</span>
          <p className="text-2xl font-bold font-mono text-rose-400 mt-2">
            {dashboard?.pipeline_health?.critical_count ?? 0}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">Overdue action gates</p>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>
              <HeartPulse className="w-4 h-4 text-rose-400" />
              Application Health Diagnostics
            </CardTitle>
            <CardDescription>
              Detailed health scores, days in stage, and automated risk recommendations.
            </CardDescription>
          </div>
        </CardHeader>

        {healthItems.length === 0 ? (
          <p className="text-xs text-slate-500 font-mono text-center py-6">
            No tracked applications to audit. Add applications to view automated health scores.
          </p>
        ) : (
          <div className="space-y-3">
            {healthItems.map((item) => (
              <div
                key={item.application_id}
                className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 hover:border-slate-700 transition"
              >
                <div className="flex items-center justify-between gap-4 flex-wrap">
                  <div className="flex items-center gap-2.5">
                    <span className="font-semibold text-sm text-slate-100">{item.company}</span>
                    <span className="text-xs text-slate-400">• {item.role}</span>
                    <Badge variant="default" size="sm">{item.status}</Badge>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-slate-400">
                      Score: <strong className="text-cyan-400">{item.health_score}/100</strong>
                    </span>
                    <Badge
                      variant={
                        item.health_status === "EXCELLENT" || item.health_status === "GOOD"
                          ? "emerald"
                          : item.health_status === "ATTENTION_NEEDED"
                          ? "amber"
                          : "rose"
                      }
                    >
                      {item.health_status}
                    </Badge>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-[11px] text-slate-400 font-mono">
                  <span>Days in current status: {item.days_in_current_status}</span>
                  {item.is_stale ? <span className="text-amber-400 font-semibold">• Stale Flagged</span> : null}
                  {item.is_overdue ? <span className="text-rose-400 font-semibold">• Overdue Action</span> : null}
                </div>

                {item.recommendations && item.recommendations.length > 0 ? (
                  <div className="pt-2 border-t border-slate-800/60 text-xs text-amber-300/90 font-sans">
                    <strong>Recommended: </strong> {item.recommendations.join(" • ")}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
