"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Volume2,
  VolumeX,
  Sparkles,
  ArrowRight,
  Terminal,
  ShieldCheck,
  Cpu,
  Layers,
  Activity,
  CheckCircle2,
  Code2,
} from "lucide-react";
import { fridayAudio } from "./FridayAudio";

interface SpatialHUDProps {
  scrollProgress: number; // 0.0 to 1.0
  hoveredNode: any | null;
  onJumpToScene: (progress: number) => void;
}

export function SpatialHUD({ scrollProgress, hoveredNode, onJumpToScene }: SpatialHUDProps) {
  const [isMuted, setIsMuted] = useState(true);
  const [hasInteracted, setHasInteracted] = useState(false);

  useEffect(() => {
    setIsMuted(fridayAudio.getMuted());
  }, []);

  const handleSoundToggle = () => {
    setHasInteracted(true);
    const muted = fridayAudio.toggleMute();
    setIsMuted(muted);
  };

  // Determine active scene
  let activeScene = 1;
  if (scrollProgress >= 0.3 && scrollProgress < 0.6) activeScene = 2;
  else if (scrollProgress >= 0.6) activeScene = 3;

  // Calculate opacities for smooth cross-fades
  // Scene 1: 1.0 at 0.0, fades out by 0.28
  const scene1Opacity = Math.max(0, Math.min(1, 1 - scrollProgress / 0.28));
  // Scene 2: fades in from 0.25 to 0.38, peaks at 0.45, fades out by 0.58
  let scene2Opacity = 0;
  if (scrollProgress >= 0.25 && scrollProgress <= 0.58) {
    if (scrollProgress < 0.42) {
      scene2Opacity = (scrollProgress - 0.25) / 0.17;
    } else {
      scene2Opacity = 1 - (scrollProgress - 0.42) / 0.16;
    }
  }
  // Scene 3: fades in from 0.52, reaches 1.0 at 0.7+
  const scene3Opacity = Math.max(0, Math.min(1, (scrollProgress - 0.52) / 0.2));

  return (
    <div className="fixed inset-0 pointer-events-none z-10 flex flex-col justify-between p-6 sm:p-10 select-none overflow-hidden text-slate-100 font-sans">
      {/* 1. TOP STATUS & NAVIGATION BAR */}
      <header className="flex items-center justify-between pointer-events-auto">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-slate-950/80 border border-cyan-500/30 backdrop-blur-md shadow-lg shadow-cyan-950/30">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_10px_#00f0ff]" />
            <span className="text-xs font-mono font-semibold tracking-wider text-slate-200">
              FRIDAY // AI OS
            </span>
            <span className="hidden sm:inline-block text-[10px] font-mono text-cyan-400/80 bg-cyan-950/60 px-2 py-0.5 rounded-md border border-cyan-800/40">
              v0.1.0 • 138/138 VERIFIED
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Audio Synthesizer Control */}
          <button
            onClick={handleSoundToggle}
            className={`px-3.5 py-1.5 rounded-full border text-xs font-mono flex items-center gap-2 transition-all backdrop-blur-md shadow-lg ${
              isMuted
                ? "bg-slate-900/60 border-slate-700/60 text-slate-400 hover:border-cyan-500/40 hover:text-slate-200"
                : "bg-cyan-950/80 border-cyan-400/50 text-cyan-300 shadow-[0_0_15px_rgba(0,240,255,0.2)]"
            }`}
            title="Toggle Procedural Audio Engine"
          >
            {isMuted ? (
              <>
                <VolumeX className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">SOUND: OFF</span>
              </>
            ) : (
              <>
                <Volume2 className="w-3.5 h-3.5 animate-pulse text-cyan-300" />
                <span className="hidden sm:inline">SOUND: ACTIVE</span>
                <span className="flex items-end gap-0.5 h-3">
                  <span className="w-0.5 h-1.5 bg-cyan-400 animate-pulse" />
                  <span className="w-0.5 h-3 bg-cyan-300 animate-pulse delay-75" />
                  <span className="w-0.5 h-2 bg-cyan-400 animate-pulse delay-150" />
                </span>
              </>
            )}
          </button>

          {/* Quick Launch Buttons */}
          <Link
            href="/chat"
            className="px-4 py-1.5 rounded-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs transition-all shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:shadow-[0_0_25px_rgba(6,182,212,0.7)] flex items-center gap-1.5"
          >
            <span>Launch Console</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </header>

      {/* 2. SCENE INDICATOR SCRUBBER (Left Margin) */}
      <aside className="fixed left-6 sm:left-10 top-1/2 -translate-y-1/2 pointer-events-auto hidden md:flex flex-col gap-5 z-20">
        {[
          { id: 1, name: "01 BOOT", target: 0.0 },
          { id: 2, name: "02 AWAKEN", target: 0.42 },
          { id: 3, name: "03 REPOSITORY", target: 0.85 },
        ].map((scene) => {
          const isActive = activeScene === scene.id;
          return (
            <button
              key={scene.id}
              onClick={() => onJumpToScene(scene.target)}
              className="group flex items-center gap-3 text-left transition-all"
            >
              <div
                className={`w-2.5 h-2.5 rounded-full border transition-all duration-300 ${
                  isActive
                    ? "bg-cyan-400 border-cyan-300 scale-125 shadow-[0_0_12px_#00f0ff]"
                    : "border-slate-600 group-hover:border-slate-400 bg-slate-900/50"
                }`}
              />
              <span
                className={`text-[11px] font-mono tracking-widest transition-all ${
                  isActive
                    ? "text-cyan-300 font-bold translate-x-1"
                    : "text-slate-500 group-hover:text-slate-300"
                }`}
              >
                {scene.name}
              </span>
            </button>
          );
        })}
      </aside>

      {/* 3. CENTER SPATIAL TYPOGRAPHY (Layered by Scene) */}
      <main className="relative flex-1 flex items-center justify-center pointer-events-none">
        {/* SCENE 01 — BOOT OVERLAY */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-center text-center px-4 transition-opacity duration-500"
          style={{ opacity: scene1Opacity, display: scene1Opacity > 0.01 ? "flex" : "none" }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/60 border border-slate-700/60 text-[11px] font-mono text-cyan-400 tracking-widest uppercase mb-6 backdrop-blur-md">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
            Autonomous Intelligence Core
          </div>

          <h1 className="text-6xl sm:text-8xl md:text-9xl font-extrabold tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white via-slate-100 to-slate-400 drop-shadow-[0_0_35px_rgba(0,240,255,0.25)]">
            FRIDAY
          </h1>

          <p className="mt-4 text-base sm:text-xl text-slate-300 font-light tracking-wide max-w-xl">
            Your autonomous software-engineering partner.
          </p>

          <div className="mt-8 flex items-center gap-3">
            <span className="text-xs font-mono text-slate-400 border-b border-cyan-500/40 pb-0.5">
              LLM PROPOSES • FRIDAY INVESTIGATES • TOOLS EXECUTE • TESTS VERIFY • HUMAN APPROVES
            </span>
          </div>

          <div className="mt-14 animate-bounce flex flex-col items-center gap-2 text-slate-500">
            <span className="text-[10px] font-mono tracking-widest uppercase">Scroll to Enter World</span>
            <div className="w-5 h-8 rounded-full border border-slate-700 flex items-start justify-center p-1">
              <span className="w-1 h-2 rounded-full bg-cyan-400 animate-pulse" />
            </div>
          </div>
        </div>

        {/* SCENE 02 — AWAKEN OVERLAY */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-center text-center px-4 transition-opacity duration-500"
          style={{ opacity: scene2Opacity, display: scene2Opacity > 0.01 ? "flex" : "none" }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-950/60 border border-purple-500/40 text-[11px] font-mono text-purple-300 tracking-widest uppercase mb-6 backdrop-blur-md shadow-lg shadow-purple-950/40">
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            Neural Synapse Engaged
          </div>

          <h2 className="text-5xl sm:text-7xl md:text-8xl font-black tracking-tight text-white drop-shadow-[0_0_40px_rgba(139,92,246,0.35)]">
            I'M FRIDAY.
          </h2>

          <p className="mt-4 text-sm sm:text-lg text-slate-300 font-normal max-w-lg leading-relaxed">
            Awakening deep intelligence across codebases, dependencies, and execution runtimes.
          </p>

          <div className="mt-8 grid grid-cols-3 gap-4 max-w-md w-full">
            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-center backdrop-blur-md">
              <p className="text-[10px] font-mono text-slate-400 uppercase">Reasoning</p>
              <p className="text-xs font-mono font-bold text-cyan-300 mt-0.5">ACTIVE</p>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-center backdrop-blur-md">
              <p className="text-[10px] font-mono text-slate-400 uppercase">AST Inspector</p>
              <p className="text-xs font-mono font-bold text-purple-300 mt-0.5">READY</p>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-center backdrop-blur-md">
              <p className="text-[10px] font-mono text-slate-400 uppercase">Self-Healing</p>
              <p className="text-xs font-mono font-bold text-rose-300 mt-0.5">ARMED</p>
            </div>
          </div>
        </div>

        {/* SCENE 03 — REPOSITORY / UNDERSTANDING OVERLAY */}
        <div
          className="absolute inset-0 flex flex-col justify-between p-4 sm:p-8 transition-opacity duration-500"
          style={{ opacity: scene3Opacity, display: scene3Opacity > 0.01 ? "flex" : "none" }}
        >
          {/* Top Left Headline */}
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/40 text-[11px] font-mono text-cyan-300 tracking-widest uppercase mb-3 backdrop-blur-md">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              Repository Universe
            </div>
            <h3 className="text-4xl sm:text-6xl font-black tracking-tight text-white drop-shadow-[0_0_30px_rgba(6,182,212,0.3)]">
              UNDERSTAND.
            </h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-300 font-light max-w-md leading-relaxed">
              Not just files. Context. Structure. Dependencies. History. Intent.
            </p>
          </div>

          {/* Right Floating Spatial Telemetry HUD */}
          <div className="self-end max-w-sm w-full space-y-2.5 pointer-events-auto">
            {hoveredNode ? (
              <div className="p-4 rounded-2xl bg-slate-950/90 border border-cyan-400/60 shadow-[0_0_30px_rgba(0,240,255,0.25)] backdrop-blur-xl transition-all animate-in fade-in zoom-in-95">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">
                    Node Inspected
                  </span>
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                </div>
                <h4 className="text-sm font-mono font-bold text-white mt-1 break-all">
                  {hoveredNode.name}
                </h4>
                <div className="mt-2 pt-2 border-t border-slate-800 flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-400">Status</span>
                  <span className="text-emerald-400 font-semibold">{hoveredNode.status}</span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-400">Symbols / Tests</span>
                  <span className="text-cyan-300">{hoveredNode.filesCount} Linked</span>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 backdrop-blur-md">
                  <p className="text-[10px] font-mono text-slate-400 uppercase">Files Indexed</p>
                  <p className="text-base font-mono font-bold text-cyan-300 mt-0.5">124 Modules</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 backdrop-blur-md">
                  <p className="text-[10px] font-mono text-slate-400 uppercase">Verification</p>
                  <p className="text-base font-mono font-bold text-emerald-300 mt-0.5">138/138 PASS</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 backdrop-blur-md">
                  <p className="text-[10px] font-mono text-slate-400 uppercase">Dependencies</p>
                  <p className="text-base font-mono font-bold text-purple-300 mt-0.5">18 Graphs</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 backdrop-blur-md">
                  <p className="text-[10px] font-mono text-slate-400 uppercase">AI Provider</p>
                  <p className="text-base font-mono font-bold text-amber-300 mt-0.5">LLaMA 3.3</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* 4. BOTTOM ACTION FOOTER */}
      <footer className="flex flex-col sm:flex-row items-center justify-between gap-4 pointer-events-auto pt-4 border-t border-slate-800/40">
        <div className="flex items-center gap-6 text-xs font-mono text-slate-500">
          <span>FRIDAY OS // BUILD 2026.09</span>
          <span className="hidden md:inline-block">SPACE KEY: AUDIO PULSE</span>
          <span className="hidden md:inline-block">DRAG / SCROLL: 3D CAMERA</span>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/chat"
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs font-mono tracking-wider transition-all shadow-[0_0_25px_rgba(6,182,212,0.4)] hover:shadow-[0_0_35px_rgba(6,182,212,0.7)] flex items-center gap-2 group"
          >
            <span>ENTER FRIDAY WORKSPACE</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </footer>
    </div>
  );
}

