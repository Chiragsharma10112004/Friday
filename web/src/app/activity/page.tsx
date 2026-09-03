"use client";

import React, { useState, useEffect } from "react";
import {
  History,
  Activity,
  CheckCircle2,
  Sparkles,
  ShieldCheck,
  RefreshCw,
  Terminal,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingSkeleton";
import { selfHealingApi, careerIntelligenceApi } from "@/lib/api";
import { SelfHealingAuditRecord, ActionItemResponse } from "@/types";
import { formatDate } from "@/lib/utils";

export default function ActivityPage() {
  const [healingHistory, setHealingHistory] = useState<SelfHealingAuditRecord[]>([]);
  const [actions, setActions] = useState<ActionItemResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [healRes, actRes] = await Promise.allSettled([
        selfHealingApi.getHistory(),
        careerIntelligenceApi.getNextActions(),
      ]);

      if (healRes.status === "fulfilled") setHealingHistory(healRes.value);
      if (actRes.status === "fulfilled") setActions(actRes.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) return <LoadingState message="Loading Unified Activity & Audit Ledger..." />;

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 font-sans flex items-center gap-2">
            <History className="w-5 h-5 text-cyan-400" />
            Unified System Activity & Audit Trail
          </h2>
          <p className="text-xs text-slate-400">
            Chronological audit ledger across autonomous workflows, self-healing events, and recommendation triggers.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>
              <Terminal className="w-4 h-4 text-cyan-400" />
              Chronological Operation Events
            </CardTitle>
            <CardDescription>All autonomous agent actions and recovery executions.</CardDescription>
          </div>
        </CardHeader>

        <div className="space-y-3">
          {healingHistory.length === 0 && actions.length === 0 ? (
            <p className="text-xs text-slate-500 font-mono text-center py-6">
              No activity records available.
            </p>
          ) : (
            <>
              {healingHistory.map((item) => (
                <div
                  key={`heal-${item.id}`}
                  className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-start justify-between gap-4 text-xs font-mono"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="rose">SELF-HEALING</Badge>
                      <span className="font-semibold text-slate-200">{item.target_file}</span>
                      <span className="text-slate-500">• {item.strategy}</span>
                    </div>
                    <p className="text-slate-400 font-sans text-xs">{item.summary}</p>
                  </div>
                  <span className="text-[10px] text-slate-500 shrink-0">{formatDate(item.timestamp)}</span>
                </div>
              ))}

              {actions.map((act) => (
                <div
                  key={`act-${act.id}`}
                  className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-start justify-between gap-4 text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="amber">RECOMMENDATION</Badge>
                      <span className="font-semibold text-slate-200">{act.title}</span>
                    </div>
                    <p className="text-slate-400 text-xs">{act.description}</p>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 shrink-0">
                    {formatDate(act.created_at)}
                  </span>
                </div>
              ))}
            </>
          )}
        </div>
      </Card>
    </div>
  );
}
