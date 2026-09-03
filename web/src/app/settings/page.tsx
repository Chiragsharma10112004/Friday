"use client";

import React, { useState, useEffect } from "react";
import {
  Settings,
  ShieldCheck,
  User,
  Save,
  CheckCircle2,
  RefreshCw,
  Cpu,
  Lock,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingSkeleton";
import { profileApi, systemApi } from "@/lib/api";
import { UserProfileResponse, SystemStatus } from "@/types";

export default function SettingsPage() {
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [title, setTitle] = useState("");
  const [skills, setSkills] = useState("");
  const [targetRoles, setTargetRoles] = useState("");
  const [targetLocations, setTargetLocations] = useState("");

  const fetchData = async () => {
    try {
      const [profRes, statRes] = await Promise.allSettled([
        profileApi.getProfile(),
        systemApi.getStatus(),
      ]);

      if (profRes.status === "fulfilled" && profRes.value) {
        setProfile(profRes.value);
        setName(profRes.value.name || "");
        setEmail(profRes.value.email || "");
        setTitle(profRes.value.title || "");
        setSkills((profRes.value.skills || []).join(", "));
        setTargetRoles((profRes.value.target_roles || []).join(", "));
        setTargetLocations((profRes.value.target_locations || []).join(", "));
      }
      if (statRes.status === "fulfilled") setStatus(statRes.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);
    try {
      await profileApi.updateProfile({
        name,
        email,
        title,
        skills: skills.split(",").map((s) => s.trim()).filter(Boolean),
        target_roles: targetRoles.split(",").map((s) => s.trim()).filter(Boolean),
        target_locations: targetLocations.split(",").map((s) => s.trim()).filter(Boolean),
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to update profile:", err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingState message="Loading System Settings & Invariants..." />;

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 font-sans flex items-center gap-2">
            <Settings className="w-5 h-5 text-cyan-400" />
            System Preferences & Safety Invariants
          </h2>
          <p className="text-xs text-slate-400">
            Candidate profile configuration, multi-model parameters, and immutable safety rules.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>
                  <User className="w-4 h-4 text-cyan-400" />
                  Candidate Profile Configuration
                </CardTitle>
                <CardDescription>
                  Used for job match scoring, resume tailoring, and form autofill.
                </CardDescription>
              </div>
            </CardHeader>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Professional Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Senior Software Engineer / AI Researcher"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Core Skills (Comma separated)</label>
                <input
                  type="text"
                  value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  placeholder="Python, FastAPI, TypeScript, React, Docker, PyTorch"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Target Roles</label>
                  <input
                    type="text"
                    value={targetRoles}
                    onChange={(e) => setTargetRoles(e.target.value)}
                    placeholder="Backend Engineer, AI Engineer"
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Target Locations</label>
                  <input
                    type="text"
                    value={targetLocations}
                    onChange={(e) => setTargetLocations(e.target.value)}
                    placeholder="Remote, San Francisco, New York"
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="pt-3 flex items-center justify-between">
                {saveSuccess ? (
                  <span className="text-xs font-mono text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Profile settings saved successfully!
                  </span>
                ) : <span />}

                <Button type="submit" variant="primary" size="md" isLoading={saving}>
                  <Save className="w-4 h-4" />
                  <span>Save Profile</span>
                </Button>
              </div>
            </form>
          </Card>
        </div>

        <div className="space-y-4">
          <Card glow="emerald">
            <CardHeader>
              <div>
                <CardTitle>
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Immutable Safety Rules
                </CardTitle>
                <CardDescription>Hardcoded security invariants</CardDescription>
              </div>
            </CardHeader>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
                  <Lock className="w-3.5 h-3.5" />
                  <span>1. Zero Credential Storage</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  FRIDAY never stores, logs, or transmits passwords, OTPs, or authentication tokens.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
                  <Lock className="w-3.5 h-3.5" />
                  <span>2. Manual Final Submission</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Final job submission strictly requires manual human confirmation.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
                  <Lock className="w-3.5 h-3.5" />
                  <span>3. AST Sandbox Confinement</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  All code edits and shell executions are restricted to safe workspace directories.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
