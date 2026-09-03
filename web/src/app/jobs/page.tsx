"use client";

import React, { useState, useEffect } from "react";
import {
  Search,
  Briefcase,
  MapPin,
  ExternalLink,
  Sparkles,
  Play,
  Filter,
  RefreshCw,
  Building2,
  DollarSign,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingSkeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { jobsApi, workflowApi } from "@/lib/api";
import { DiscoveredJob } from "@/types";

export default function JobsPage() {
  const [opportunities, setOpportunities] = useState<DiscoveredJob[]>([]);
  const [loading, setLoading] = useState(true);

  const [roleQuery, setRoleQuery] = useState("Software Engineer");
  const [locationQuery, setLocationQuery] = useState("");
  const [providerQuery, setProviderQuery] = useState("all");
  const [searching, setSearching] = useState(false);

  const fetchOpportunities = async () => {
    try {
      const res = await jobsApi.listOpportunities({ page_size: 50 });
      setOpportunities(res.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpportunities();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!roleQuery.trim()) return;
    setSearching(true);
    try {
      const res = await jobsApi.searchJobs({
        role: roleQuery.trim(),
        location: locationQuery.trim() || undefined,
        provider: providerQuery === "all" ? undefined : providerQuery,
      });
      setOpportunities(res.opportunities);
    } catch (err) {
      console.error("Job search failed:", err);
    } finally {
      setSearching(false);
    }
  };

  const handleLaunchWorkflow = async (job: DiscoveredJob) => {
    try {
      await workflowApi.createFromOpportunity(job.id, "HIGH");
      alert(`Autonomous Workflow launched for ${job.company} - ${job.title}!`);
    } catch (err) {
      console.error("Failed to launch workflow:", err);
    }
  };

  if (loading) return <LoadingState message="Discovering opportunities across Greenhouse, Lever & Workday..." />;

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 font-sans flex items-center gap-2">
            <Search className="w-5 h-5 text-emerald-400" />
            Multi-Platform Job Discovery
          </h2>
          <p className="text-xs text-slate-400">
            Automated scraping, ATS parsing, skill matching, and 1-click workflow dispatch.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchOpportunities}>
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Opportunities</span>
        </Button>
      </div>

      <Card glow="emerald">
        <form onSubmit={handleSearch} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium text-slate-300 mb-1">Target Role / Keyword</label>
            <input
              type="text"
              required
              value={roleQuery}
              onChange={(e) => setRoleQuery(e.target.value)}
              placeholder="e.g. Backend Engineer, Full Stack, Python"
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Location</label>
            <input
              type="text"
              value={locationQuery}
              onChange={(e) => setLocationQuery(e.target.value)}
              placeholder="e.g. Remote, San Francisco"
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="flex items-end">
            <Button
              type="submit"
              variant="success"
              size="md"
              isLoading={searching}
              className="w-full"
            >
              <Search className="w-4 h-4" />
              <span>Discover Jobs</span>
            </Button>
          </div>
        </form>
      </Card>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">
            Discovered Opportunities ({opportunities.length})
          </h3>
        </div>

        {opportunities.length === 0 ? (
          <EmptyState
            icon={Search}
            title="No jobs discovered"
            description="Run a discovery search across Greenhouse or Lever to extract live job listings."
            actionLabel="Discover Software Roles"
            onAction={fetchOpportunities}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {opportunities.map((job) => (
              <Card key={job.id} hoverEffect className="space-y-4 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h4 className="text-sm font-bold text-slate-100">{job.title}</h4>
                      <p className="text-xs text-emerald-400 font-medium flex items-center gap-1.5 mt-0.5">
                        <Building2 className="w-3.5 h-3.5" />
                        {job.company}
                      </p>
                    </div>

                    {job.match_score ? (
                      <Badge variant="emerald" size="md">
                        {Math.round(job.match_score * 100)}% Match
                      </Badge>
                    ) : (
                      <Badge variant="cyan" size="sm">{job.provider}</Badge>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-500" />
                      {job.location || "Remote"}
                    </span>
                    {job.salary_range ? (
                      <span className="flex items-center gap-1 text-amber-300">
                        <DollarSign className="w-3.5 h-3.5" />
                        {job.salary_range}
                      </span>
                    ) : null}
                  </div>

                  {job.skills_required && job.skills_required.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {job.skills_required.slice(0, 4).map((skill, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] text-slate-400 font-mono"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-3">
                  <a
                    href={job.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1"
                  >
                    <span>View Post</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleLaunchWorkflow(job)}
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>Launch Workflow</span>
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
