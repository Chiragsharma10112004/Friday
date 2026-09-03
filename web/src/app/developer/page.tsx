"use client";

import React, { useState, useEffect } from "react";
import {
  Code2,
  Play,
  Search,
  FileCode,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FolderTree,
  Terminal,
  Cpu,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DiffViewer } from "@/components/ui/DiffViewer";
import { LoadingState } from "@/components/ui/LoadingSkeleton";
import { developerApi } from "@/lib/api";
import { WorkspaceMap, SymbolDefinition, TestRunReport, CodeEditResponse } from "@/types";

export default function DeveloperPage() {
  const [workspace, setWorkspace] = useState<WorkspaceMap | null>(null);
  const [symbols, setSymbols] = useState<SymbolDefinition[]>([]);
  const [symbolSearch, setSymbolSearch] = useState("");
  const [loadingWorkspace, setLoadingWorkspace] = useState(true);

  const [testTarget, setTestTarget] = useState("tests.run_all_phase_tests");
  const [runningTests, setRunningTests] = useState(false);
  const [testReport, setTestReport] = useState<TestRunReport | null>(null);

  const [funcName, setFuncName] = useState("");
  const [instruction, setInstruction] = useState("");
  const [editingCode, setEditingCode] = useState(false);
  const [editResult, setEditResult] = useState<CodeEditResponse | null>(null);

  const loadWorkspace = async () => {
    setLoadingWorkspace(true);
    try {
      const data = await developerApi.getWorkspace(".");
      setWorkspace(data);
    } catch (err) {
      console.error("Failed to load workspace:", err);
    } finally {
      setLoadingWorkspace(false);
    }
  };

  const handleSymbolSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbolSearch.trim()) return;
    try {
      const data = await developerApi.lookupSymbols(symbolSearch.trim(), ".");
      setSymbols(data);
    } catch (err) {
      console.error("Failed to lookup symbols:", err);
    }
  };

  const handleRunTests = async () => {
    setRunningTests(true);
    try {
      const report = await developerApi.runTests(testTarget, 120);
      setTestReport(report);
    } catch (err: any) {
      console.error("Test run failed:", err);
      setTestReport({
        total_run: 0,
        passed: 0,
        failed: 1,
        errors: 0,
        duration_sec: 0,
        success: false,
        test_cases: [],
        raw_output: err?.message || "Failed to execute test runner subprocess",
      });
    } finally {
      setRunningTests(false);
    }
  };

  const handleCodeEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!funcName.trim() || !instruction.trim()) return;
    setEditingCode(true);
    setEditResult(null);
    try {
      const res = await developerApi.editCode({
        function_name: funcName.trim(),
        instruction: instruction.trim(),
        preview: true,
      });
      setEditResult(res);
    } catch (err: any) {
      console.error("Code edit failed:", err);
      setEditResult({
        success: false,
        error: err?.message || "Failed to perform AST function edit",
      });
    } finally {
      setEditingCode(false);
    }
  };

  useEffect(() => {
    loadWorkspace();
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 font-sans flex items-center gap-2">
            <Code2 className="w-5 h-5 text-cyan-400" />
            Developer Intelligence & AST Inspector
          </h2>
          <p className="text-xs text-slate-400">
            Confined AST repository parser, symbol indexer, and safe subprocess test runner.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadWorkspace}>
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Reload AST Map</span>
        </Button>
      </div>

      <Card glow="cyan">
        <CardHeader>
          <div>
            <CardTitle>
              <Terminal className="w-4 h-4 text-cyan-400" />
              Safe Test Subprocess Runner
            </CardTitle>
            <CardDescription>
              Execute unit & integration test suites inside confined sandbox with structured output.
            </CardDescription>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={handleRunTests}
            isLoading={runningTests}
          >
            <Play className="w-3.5 h-3.5" />
            <span>Run Test Suite</span>
          </Button>
        </CardHeader>

        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-slate-400">Target Module:</span>
            <input
              type="text"
              value={testTarget}
              onChange={(e) => setTestTarget(e.target.value)}
              className="flex-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-700 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {testReport ? (
            <div className="space-y-4 pt-2">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 font-mono">TOTAL TESTS</span>
                  <p className="text-lg font-bold font-mono text-slate-200">{testReport.total_run}</p>
                </div>
                <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/60">
                  <span className="text-[10px] text-emerald-400 font-mono">PASSED</span>
                  <p className="text-lg font-bold font-mono text-emerald-300">{testReport.passed}</p>
                </div>
                <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60">
                  <span className="text-[10px] text-rose-400 font-mono">FAILURES / ERRORS</span>
                  <p className="text-lg font-bold font-mono text-rose-300">
                    {testReport.failed + testReport.errors}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 font-mono">DURATION</span>
                  <p className="text-lg font-bold font-mono text-cyan-400">{testReport.duration_sec.toFixed(2)}s</p>
                </div>
              </div>

              <div>
                <span className="text-xs font-mono text-slate-400 mb-1 block">Subprocess Output Log:</span>
                <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300 max-h-48 overflow-y-auto whitespace-pre-wrap">
                  {testReport.raw_output || "Test execution completed cleanly."}
                </pre>
              </div>
            </div>
          ) : null}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="space-y-4">
          <CardHeader>
            <div>
              <CardTitle>
                <FolderTree className="w-4 h-4 text-purple-400" />
                AST Workspace Map
              </CardTitle>
              <CardDescription>
                {workspace ? `${workspace.total_files} files analyzed • ${workspace.total_lines} lines of code` : "Analyzing codebase..."}
              </CardDescription>
            </div>
          </CardHeader>

          <form onSubmit={handleSymbolSearch} className="flex gap-2">
            <input
              type="text"
              placeholder="Search AST symbol (e.g. diagnose, default_pipeline_service)..."
              value={symbolSearch}
              onChange={(e) => setSymbolSearch(e.target.value)}
              className="flex-1 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
            <Button type="submit" variant="secondary" size="sm">
              <Search className="w-3.5 h-3.5" />
              <span>Search</span>
            </Button>
          </form>

          {symbols.length > 0 ? (
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              <span className="text-[11px] font-mono text-slate-400">Search Results ({symbols.length}):</span>
              {symbols.map((sym, i) => (
                <div key={i} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1 font-mono">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-cyan-400">{sym.name}</span>
                    <Badge variant="default" size="sm">{sym.symbol_type}</Badge>
                  </div>
                  <p className="text-[10px] text-slate-500">{sym.file} : line {sym.line}</p>
                </div>
              ))}
            </div>
          ) : null}

          {loadingWorkspace ? (
            <LoadingState message="Inspecting workspace files..." />
          ) : (
            <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
              {workspace?.files.slice(0, 15).map((f) => (
                <div
                  key={f.path}
                  className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs hover:border-slate-700 transition font-mono"
                >
                  <div className="flex items-center gap-2">
                    <FileCode className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-slate-200">{f.path}</span>
                  </div>
                  <span className="text-[10px] text-slate-500">{f.lines_count} lines • {f.symbols_count} symbols</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="space-y-4">
          <CardHeader>
            <div>
              <CardTitle>
                <Sparkles className="w-4 h-4 text-cyan-400" />
                AST Code Modification Agent
              </CardTitle>
              <CardDescription>
                Propose and preview unified AST diffs safely with Natural Language.
              </CardDescription>
            </div>
          </CardHeader>

          <form onSubmit={handleCodeEdit} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Target Function Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. calculate_score"
                value={funcName}
                onChange={(e) => setFuncName(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Editing Instruction *</label>
              <textarea
                rows={3}
                required
                placeholder="Describe the AST code change (e.g. add a defensive check for None inputs and return 0)..."
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 resize-none font-sans"
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={editingCode}
              className="w-full"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Generate Diff Preview</span>
            </Button>
          </form>

          {editResult ? (
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-200">Unified Diff Preview:</span>
                <Badge variant={editResult.success ? "emerald" : "rose"}>
                  {editResult.success ? "Diff Valid" : "Edit Error"}
                </Badge>
              </div>

              {editResult.success && editResult.diff ? (
                <DiffViewer diffText={editResult.diff} />
              ) : (
                <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 font-mono">
                  {editResult.error || "Failed to generate valid AST modification."}
                </div>
              )}
            </div>
          ) : null}
        </Card>
      </div>
    </div>
  );
}
