"use client";

import React, { useState, useEffect } from "react";
import "./globals.css";
import { Sidebar } from "@/components/shell/Sidebar";
import { Topbar } from "@/components/shell/Topbar";
import { CommandPalette } from "@/components/shell/CommandPalette";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <html lang="en" className="dark">
      <head>
        <title>FRIDAY — Autonomous AI Personal Operating System</title>
        <meta
          name="description"
          content="FRIDAY Autonomous AI Personal Operating System — Intelligence, Code Editing, Self-Healing, and Career Workflows"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="bg-background text-slate-100 min-h-screen antialiased selection:bg-cyan-500/30 selection:text-cyan-200">
        <div className="flex min-h-screen">
          <Sidebar />

          <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
            <Topbar
              onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
            />

            <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
              {children}
            </main>
          </div>
        </div>

        <CommandPalette
          isOpen={isCommandPaletteOpen}
          onClose={() => setIsCommandPaletteOpen(false)}
        />
      </body>
    </html>
  );
}
