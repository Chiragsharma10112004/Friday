"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { SpatialHUD } from "@/components/cinematic/SpatialHUD";
import { fridayAudio } from "@/components/cinematic/FridayAudio";

// Dynamically import Three.js canvas with SSR disabled to ensure WebGL context safety
const FridayCanvas = dynamic(
  () =>
    import("@/components/cinematic/FridayCanvas").then((mod) => mod.FridayCanvas),
  {
    ssr: false,
    loading: () => (
      <div className="fixed inset-0 z-0 bg-black flex items-center justify-center pointer-events-none">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin" />
          <span className="text-xs font-mono text-cyan-400/80 tracking-widest uppercase">
            Initializing WebGL Engine...
          </span>
        </div>
      </div>
    ),
  }
);

export default function CinematicHomePage() {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [hoveredNode, setHoveredNode] = useState<any | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Smooth scroll progress calculation
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY || window.pageYOffset;
      const maxScroll =
        document.documentElement.scrollHeight - window.innerHeight;
      const progress =
        maxScroll > 0 ? Math.min(1, Math.max(0, scrollY / maxScroll)) : 0;
      setScrollProgress(progress);

      // Modulate spatial audio engine with scroll velocity/position
      fridayAudio.updateScroll(progress);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Jump to specific scene helper
  const handleJumpToScene = useCallback((targetProgress: number) => {
    const maxScroll =
      document.documentElement.scrollHeight - window.innerHeight;
    const targetScrollY = targetProgress * maxScroll;
    window.scrollTo({
      top: targetScrollY,
      behavior: "smooth",
    });
    fridayAudio.playClick(1000);
  }, []);

  // Keyboard shortcut listener for spatial sound interaction
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" && e.target === document.body) {
        e.preventDefault();
        fridayAudio.triggerDataBlip(1800, 0.08);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div
      ref={scrollContainerRef}
      className="relative min-h-[350vh] bg-black text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200"
    >
      {/* 1. Persistent 3D WebGL Canvas Layer */}
      <FridayCanvas
        scrollProgress={scrollProgress}
        onNodeHover={setHoveredNode}
      />

      {/* 2. Floating Spatial HUD Interface */}
      <SpatialHUD
        scrollProgress={scrollProgress}
        hoveredNode={hoveredNode}
        onJumpToScene={handleJumpToScene}
      />

      {/* 3. Invisible Spatial Scroll Anchor Milestones */}
      <div className="relative pointer-events-none">
        <div id="scene-01-boot" className="h-screen" />
        <div id="scene-02-awaken" className="h-screen" />
        <div id="scene-03-repository" className="h-[150vh]" />
      </div>
    </div>
  );
}
