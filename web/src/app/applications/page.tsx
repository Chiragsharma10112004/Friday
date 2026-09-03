"use client";

import React, { useState, useEffect } from "react";
import {
  Briefcase,
  Plus,
  Filter,
  RefreshCw,
  ExternalLink,
  MessageSquare,
  Clock,
  CheckCircle2,
  Calendar,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { LoadingState } from "@/components/ui/LoadingSkeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { applicationsApi } from "@/lib/api";
import {
  ApplicationResponse,
  PipelineSummaryResponse,
  ApplicationTimelineEventResponse,
} from "@/types";
import { formatDate } from "@/lib/utils";

const PIPELINE_COLUMNS = [
  { id: "SAVED", label: "Saved" },
  { id: "APPLIED", label: "Applied" },
  { id: "SCREENING", label: "Screening" },
  { id: "TECHNICAL", label: "Technical" },
  { id: "FINAL_ROUND", label: "Final Round" },
  { id: "OFFER", label: "Offer" },
  { id: "REJECTED", label: "Rejected" },
];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [summary, setSummary] = useState<PipelineSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const [selectedApp, setSelectedApp] = useState<ApplicationResponse | null>(null);
  const [timeline, setTimeline] = useState<ApplicationTimelineEventResponse[]>([]);
  const [noteText, setNoteText] = useState("");
  const [addingNote, setAddingNote] = useState(false);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newCompany, setNewCompany] = useState("");
  const [newRole, setNewRole] = useState("");
  const [newSourceUrl, setNewSourceUrl] = useState("");
  const [newStatus, setNewStatus] = useState("SAVED");
  const [creating, setCreating] = useState(false);

  const fetchData = async () => {
    try {
      const [listRes, sumRes] = await Promise.allSettled([
        applicationsApi.listApplications({ page_size: 100 }),
        applicationsApi.getSummary(),
      ]);

      if (listRes.status === "fulfilled") setApplications(listRes.value.items);
      if (sumRes.status === "fulfilled") setSummary(sumRes.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenDetail = async (app: ApplicationResponse) => {
    setSelectedApp(app);
    try {
      const tEvents = await applicationsApi.getTimeline(app.id);
      setTimeline(tEvents);
    } catch (err) {
      console.error("Failed to load timeline:", err);
    }
  };

  const handleStatusChange = async (appId: number, newStatus: string) => {
    try {
      await applicationsApi.transitionStatus(appId, newStatus, "Status updated from Kanban board");
      fetchData();
      if (selectedApp && selectedApp.id === appId) {
        setSelectedApp({ ...selectedApp, status: newStatus });
        const tEvents = await applicationsApi.getTimeline(appId);
        setTimeline(tEvents);
      }
    } catch (err) {
      console.error("Status update failed:", err);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApp || !noteText.trim()) return;
    setAddingNote(true);
    try {
      await applicationsApi.addNote(selectedApp.id, noteText.trim());
      setNoteText("");
      const tEvents = await applicationsApi.getTimeline(selectedApp.id);
      setTimeline(tEvents);
    } catch (err) {
      console.error("Failed to add note:", err);
    } finally {
      setAddingNote(false);
    }
  };

  const handleCreateApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompany || !newRole) return;
    setCreating(true);
    try {
      await applicationsApi.createApplication({
        company: newCompany,
        role: newRole,
        source_url: newSourceUrl || undefined,
        status: newStatus,
      });
      setIsCreateOpen(false);
      setNewCompany("");
      setNewRole("");
      setNewSourceUrl("");
      fetchData();
    } catch (err) {
      console.error("Failed to create application:", err);
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <LoadingState message="Loading Applications Kanban Board..." />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 font-sans flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-cyan-400" />
            Application Lifecycle Pipeline
          </h2>
          <p className="text-xs text-slate-400">
            Kanban workflow tracking from saved opportunity to final offer.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </Button>
          <Button variant="primary" size="sm" onClick={() => setIsCreateOpen(true)}>
            <Plus className="w-4 h-4" />
            <span>New Application</span>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-[10px] text-slate-500 font-mono">TOTAL APPLICATIONS</span>
          <p className="text-xl font-bold font-mono text-slate-100 mt-0.5">
            {summary?.total_applications ?? applications.length}
          </p>
        </div>
        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-[10px] text-slate-500 font-mono">APPLIED</span>
          <p className="text-xl font-bold font-mono text-cyan-400 mt-0.5">
            {summary?.status_counts?.APPLIED ?? 0}
          </p>
        </div>
        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-[10px] text-slate-500 font-mono">INTERVIEWS</span>
          <p className="text-xl font-bold font-mono text-purple-400 mt-0.5">
            {(summary?.status_counts?.SCREENING ?? 0) + (summary?.status_counts?.TECHNICAL ?? 0)}
          </p>
        </div>
        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
          <span className="text-[10px] text-slate-500 font-mono">OFFERS</span>
          <p className="text-xl font-bold font-mono text-emerald-400 mt-0.5">
            {summary?.status_counts?.OFFER ?? 0}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-7 gap-3 overflow-x-auto pb-4">
        {PIPELINE_COLUMNS.map((col) => {
          const colApps = applications.filter((a) => a.status === col.id);
          return (
            <div key={col.id} className="min-w-[200px] flex flex-col space-y-2">
              <div className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800">
                <span className="text-xs font-semibold text-slate-300">{col.label}</span>
                <span className="text-[10px] font-mono text-slate-500 px-1.5 py-0.5 rounded bg-slate-800">
                  {colApps.length}
                </span>
              </div>

              <div className="space-y-2">
                {colApps.map((app) => (
                  <div
                    key={app.id}
                    onClick={() => handleOpenDetail(app)}
                    className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-900/90 cursor-pointer transition space-y-2 shadow-sm"
                  >
                    <div>
                      <h4 className="text-xs font-bold text-slate-100 line-clamp-1">{app.company}</h4>
                      <p className="text-[11px] text-slate-400 line-clamp-1">{app.role}</p>
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-800/60">
                      <span>{app.priority}</span>
                      <span>{formatDate(app.created_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {selectedApp ? (
        <Modal
          isOpen={!!selectedApp}
          onClose={() => setSelectedApp(null)}
          title={`${selectedApp.company} — ${selectedApp.role}`}
          description={`Application ID: #${selectedApp.id} • Created: ${formatDate(selectedApp.created_at)}`}
          maxWidth="2xl"
        >
          <div className="space-y-6">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-medium text-slate-400">Current Status:</span>
              <select
                value={selectedApp.status}
                onChange={(e) => handleStatusChange(selectedApp.id, e.target.value)}
                className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-cyan-400 font-semibold focus:outline-none focus:border-cyan-500"
              >
                {PIPELINE_COLUMNS.map((col) => (
                  <option key={col.id} value={col.id}>
                    {col.label}
                  </option>
                ))}
              </select>
            </div>

            <form onSubmit={handleAddNote} className="space-y-2">
              <label className="block text-xs font-medium text-slate-300">Add Timeline Note</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. Sent follow-up email to recruiter, technical screen scheduled for Tuesday..."
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  className="flex-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                />
                <Button type="submit" variant="primary" size="sm" isLoading={addingNote}>
                  Add Note
                </Button>
              </div>
            </form>

            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-300">Application Timeline Events</h4>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {timeline.map((event) => (
                  <div
                    key={event.id}
                    className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs font-mono space-y-0.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-cyan-400">{event.event_type}</span>
                      <span className="text-[10px] text-slate-500">{formatDate(event.timestamp)}</span>
                    </div>
                    <p className="text-slate-300 font-sans">{event.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      ) : null}

      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Add Application Track"
        description="Manually record a job opportunity into your pipeline."
      >
        <form onSubmit={handleCreateApplication} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Company Name *</label>
            <input
              type="text"
              required
              placeholder="e.g. OpenAI, Microsoft"
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
              placeholder="e.g. AI Research Engineer"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Status</label>
            <select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              {PIPELINE_COLUMNS.map((col) => (
                <option key={col.id} value={col.id}>
                  {col.label}
                </option>
              ))}
            </select>
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <Button variant="outline" size="sm" type="button" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={creating}>
              Save Application
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
