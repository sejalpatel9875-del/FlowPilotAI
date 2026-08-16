"use client";

import "./globals.css";
import React from "react";
import { Providers, useTheme } from "./providers";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { AmbientCanvasBackground } from "@/components/ui/AmbientCanvasBackground";

function MainLayoutShell({ children }: { children: React.ReactNode }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="relative flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* Subtle GPU Atmospheric Motion Canvas */}
      <AmbientCanvasBackground />

      {/* Desktop Left Persistent Sidebar */}
      <Sidebar className="hidden md:flex relative z-20" />

      {/* Main Content Viewport */}
      <div className="flex flex-1 flex-col overflow-hidden relative z-10">
        <Topbar isDark={theme === "dark"} onToggleTheme={toggleTheme} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <title>FlowPilot AI - Autonomous Multi-Agent Orchestrator</title>
        <meta
          name="description"
          content="Autonomous multi-agent orchestration, workflow intelligence, and freelancing operating system powered by NVIDIA Nemotron 3 Ultra."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <Providers>
          <MainLayoutShell>{children}</MainLayoutShell>
        </Providers>
      </body>
    </html>
  );
}
