"use client";

import React, { useState, useEffect } from "react";
import {
  CheckSquare,
  Play,
  Pause,
  RotateCcw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Plus,
  Filter,
  RefreshCw,
  Clock,
  ShieldAlert,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { LoadingState } from "@/components/ui/LoadingSkeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { workflowApi, careerIntelligenceApi } from "@/lib/api";
import { WorkflowResponse, ActionItemResponse } from "@/types";
import { formatDate } from "@/lib/utils";

export default function TasksPage() {
  const [workflows, setWorkflows] = useState<WorkflowResponse[]>([]);
  const [recommendations, setRecommendations] = useState<ActionItemResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [newCompany, setNewCompany] = useState("");
  const [newRole, setNewRole] = useState("");
  const [newSourceUrl, setNewSourceUrl] = useState("");
  const [newPriority, setNewPriority] = useState("HIGH");
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      const [wfRes, recRes] = await Promise.allSettled([
        workflowApi.listWorkflows({ limit: 50 }),
        careerIntelligenceApi.getNextActions(),
      ]);

      if (wfRes.status === "fulfilled") setWorkflows(wfRes.value.items);
      if (recRes.status === "fulfilled") setRecommendations(recRes.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompany || !newRole) return;
    setSubmitting(true);
    try {
      await workflowApi.createWorkflow({
        company: newCompany,
        role: newRole,
        source_url: newSourceUrl || undefined,
        priority: newPriority,
      });
      setIsModalOpen(false);
      setNewCompany("");
      setNewRole("");
      setNewSourceUrl("");
      fetchData();
    } catch (err) {
      console.error("Failed to create workflow:", err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartWorkflow = async (id: number) => {
    try {
      await workflowApi.startWorkflow(id);
      fetchData();
    } catch (err) {
      console.error("Start failed:", err);
    }
  };

  const handleApproveCheckpoint = async (id: number) => {
    try {
      await workflowApi.approveCheckpoint(id, { reason: "Approved by Operator" });
      fetchData();
    } catch (err) {
      console.error("Approve failed:", err);
    }
  };

  const handlePauseWorkflow = async (id: number) => {
    try {
      await workflowApi.pauseWorkflow(id);
      fetchData();
    } catch (err) {
      console.error("Pause failed:", err);
    }
  };

  const handleResumeWorkflow = async (id: number) => {
    try {
      await workflowApi.resumeWorkflow(id);
      fetchData();
    } catch (err) {
      console.error("Resume failed:", err);
    }
  };

  const handleCompleteRecommendation = async (id: number) => {
    try {
      await careerIntelligenceApi.completeRecommendation(id);
      fetchData();
    } catch (err) {
      console.error("Complete failed:", err);
    }
  };

  if (loading) return <LoadingState message="Loading Autonomous Workflows & Task Plans..." />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 font-sans flex items-center gap-2">
            <CheckSquare className="w-5 h-5 text-cyan-400" />
            Autonomous Workflows & Task Queue
          </h2>
          <p className="text-xs text-slate-400">
            Multi-stage autonomous execution pipelines with strict human approval checkpoints.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </Button>
          <Button variant="primary" size="sm" onClick={() => setIsModalOpen(true)}>
            <Plus className="w-4 h-4" />
            <span>New Workflow</span>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200">Active Workflows ({workflows.length})</h3>
          </div>

          {workflows.length === 0 ? (
            <EmptyState
              icon={CheckSquare}
              title="No active workflows"
              description="Create a new autonomous workflow to orchestrate application asset generation and submission checkpoints."
              actionLabel="Create Workflow"
              onAction={() => setIsModalOpen(true)}
            />
          ) : (
            <div className="space-y-3">
              {workflows.map((wf) => {
                const isPendingApproval = wf.user_action_required || wf.status === "AWAITING_APPROVAL";
                const isPaused = wf.status === "PAUSED";
                const isRunning = wf.status === "IN_PROGRESS" || wf.status === "RUNNING";

                return (
                  <Card key={wf.id} className="space-y-3" glow={isPendingApproval ? "amber" : "none"}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-sm text-slate-100">{wf.company}</span>
                          <span className="text-xs text-slate-400">• {wf.role}</span>
                          <Badge
                            variant={
                              wf.priority === "CRITICAL"
                                ? "rose"
                                : wf.priority === "HIGH"
                                ? "amber"
                                : "cyan"
                            }
                          >
                            {wf.priority}
                          </Badge>
                          <Badge
                            variant={
                              wf.status === "COMPLETED"
                                ? "emerald"
                                : isPendingApproval
                                ? "amber"
                                : isRunning
                                ? "cyan"
                                : "default"
                            }
                          >
                            {wf.status}
                          </Badge>
                        </div>
                        <p className="text-[11px] font-mono text-slate-500">
                          ID: #{wf.id} • Platform: {wf.source_platform} • Step: {wf.current_step || "Initialized"}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {isPendingApproval ? (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleApproveCheckpoint(wf.id)}
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Approve Gate</span>
                          </Button>
                        ) : null}

                        {wf.status === "CREATED" ? (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleStartWorkflow(wf.id)}
                          >
                            <Play className="w-3.5 h-3.5" />
                            <span>Start</span>
                          </Button>
                        ) : null}

                        {isRunning ? (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handlePauseWorkflow(wf.id)}
                          >
                            <Pause className="w-3.5 h-3.5" />
                            <span>Pause</span>
                          </Button>
                        ) : null}

                        {isPaused ? (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleResumeWorkflow(wf.id)}
                          >
                            <Play className="w-3.5 h-3.5" />
                            <span>Resume</span>
                          </Button>
                        ) : null}
                      </div>
                    </div>

                    {wf.pending_approvals && wf.pending_approvals.length > 0 ? (
                      <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-800/60 flex items-center justify-between text-xs text-amber-300">
                        <div className="flex items-center gap-2">
                          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
                          <span>
                            Human Approval Required: <strong>{wf.pending_approvals[0].approval_type}</strong>
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-amber-400/80">
                          {formatDate(wf.pending_approvals[0].requested_at)}
                        </span>
                      </div>
                    ) : null}
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-200">Recommended Next Steps</h3>
          <div className="space-y-2.5">
            {recommendations.length === 0 ? (
              <p className="text-xs text-slate-500 font-mono p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                No active recommendations.
              </p>
            ) : (
              recommendations.map((rec) => (
                <Card key={rec.id} className="p-3.5 space-y-2">
                  <div className="flex items-center justify-between">
                    <Badge
                      variant={
                        rec.priority === "CRITICAL"
                          ? "rose"
                          : rec.priority === "HIGH"
                          ? "amber"
                          : "cyan"
                      }
                    >
                      {rec.priority}
                    </Badge>
                    <span className="text-[10px] font-mono text-slate-500">
                      {formatDate(rec.created_at)}
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-slate-200">{rec.title}</h4>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{rec.description}</p>
                  <div className="pt-2 flex justify-end">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleCompleteRecommendation(rec.id)}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Complete</span>
                    </Button>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Autonomous Workflow"
        description="Launch an orchestrated multi-stage pipeline for a target role."
      >
        <form onSubmit={handleCreateWorkflow} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Company *</label>
            <input
              type="text"
              required
              placeholder="e.g. Google, Stripe, Anthropic"
              value={newCompany}
              onChange={(e) => setNewCompany(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Role Title *</label>
            <input
              type="text"
              required
              placeholder="e.g. Senior Software Engineer"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Source URL (Optional)</label>
            <input
              type="url"
              placeholder="https://boards.greenhouse.io/..."
              value={newSourceUrl}
              onChange={(e) => setNewSourceUrl(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Priority</label>
            <select
              value={newPriority}
              onChange={(e) => setNewPriority(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <Button variant="outline" size="sm" type="button" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={submitting}>
              Create Workflow
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
