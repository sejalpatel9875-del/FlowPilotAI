"use client";

import "./globals.css";
import React from "react";
import { Providers, useTheme } from "./providers";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

function MainLayoutShell({ children }: { children: React.ReactNode }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* Desktop Left Sidebar */}
      <Sidebar className="hidden md:flex" />

      {/* Main Content Viewport */}
      <div className="flex flex-1 flex-col overflow-hidden">
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
        <title>FlowPilot AI - Freelancing & Productivity OS</title>
        <meta
          name="description"
          content="AI-powered Freelancing, Growth, Productivity and Learning Operating System for modern developers and independent professionals."
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
