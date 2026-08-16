"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "@/app/providers";
import { cn } from "@/utils/cn";
import {
  Sparkles,
  LayoutDashboard,
  Users,
  Send,
  Clock,
  UserCheck,
  Briefcase,
  CheckSquare,
  GraduationCap,
  BookOpen,
  Bot,
  Zap,
  BarChart3,
  Shield,
  Layers,
  Settings,
  ChevronRight,
  ShieldCheck,
  ZapIcon,
  Palette,
  Activity,
  Terminal,
  Key,
  Sliders,
  Cpu,
  Lock,
} from "lucide-react";

export const sidebarSections = [
  {
    category: "COMMAND",
    items: [
      { name: "Command Center", href: "/command-center", icon: <Sparkles className="h-4 w-4 text-primary" />, badge: "LIVE" },
      { name: "AI Workforce", href: "/", icon: <Cpu className="h-4 w-4 text-sky-400" /> },
    ],
  },
  {
    category: "ORCHESTRATION",
    items: [
      { name: "Workflow Intelligence", href: "/workflows", icon: <Layers className="h-4 w-4 text-secondary" />, badge: "DAG" },
      { name: "Automations", href: "/automations", icon: <Zap className="h-4 w-4 text-amber-400" /> },
    ],
  },
  {
    category: "AGENT FLEET",
    items: [
      { name: "Fleet Control (12)", href: "/agents", icon: <Bot className="h-4 w-4 text-indigo-400" />, badge: "12 Active" },
      { name: "Skill Accelerator", href: "/learning", icon: <GraduationCap className="h-4 w-4 text-emerald-400" /> },
      { name: "Knowledge Vault", href: "/knowledge", icon: <BookOpen className="h-4 w-4 text-secondary" /> },
    ],
  },
  {
    category: "HUMAN CONTROL",
    items: [
      { name: "Decision Gates", href: "/approvals", icon: <ShieldCheck className="h-4 w-4 text-amber-400" />, badge: "Gate" },
    ],
  },
  {
    category: "BUSINESS INTELLIGENCE",
    items: [
      { name: "Lead Intelligence", href: "/leads", icon: <Users className="h-4 w-4 text-emerald-400" /> },
      { name: "Personalized Outreach", href: "/outreach", icon: <Send className="h-4 w-4 text-primary" /> },
      { name: "Follow-up Cadences", href: "/follow-ups", icon: <Clock className="h-4 w-4 text-rose-400" /> },
      { name: "Client CRM", href: "/clients", icon: <UserCheck className="h-4 w-4 text-tertiary" /> },
      { name: "Projects & Scopes", href: "/projects", icon: <Briefcase className="h-4 w-4 text-sky-400" /> },
      { name: "Focus & Tasks", href: "/tasks", icon: <CheckSquare className="h-4 w-4 text-amber-400" /> },
    ],
  },
  {
    category: "OBSERVABILITY",
    items: [
      { name: "AI Telemetry & Health", href: "/analytics", icon: <Activity className="h-4 w-4 text-tertiary" />, badge: "99.4%" },
    ],
  },
  {
    category: "SECURITY & GOVERNANCE",
    items: [
      { name: "Trust & Security", href: "/security", icon: <Shield className="h-4 w-4 text-rose-400" />, badge: "100%" },
      { name: "Access & Keys", href: "/settings/security", icon: <Key className="h-4 w-4 text-muted-foreground" /> },
    ],
  },
  {
    category: "SYSTEM",
    items: [
      { name: "Integrations & NIM", href: "/integrations", icon: <ZapIcon className="h-4 w-4 text-sky-400" /> },
      { name: "System Settings", href: "/settings", icon: <Settings className="h-4 w-4 text-muted-foreground" /> },
    ],
  },
];

export interface SidebarProps {
  className?: string;
  onMobileNavigate?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ className, onMobileNavigate }) => {
  const pathname = usePathname();
  const { openStudio, themeConfig } = useTheme();

  return (
    <aside
      className={cn(
        "flex flex-col h-full w-64 glass-panel bg-surface-lowest/95 border-r border-border/80 text-foreground overflow-hidden select-none shrink-0 z-20",
        className
      )}
    >
      {/* Brand Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-border/60 bg-surface/50">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-primary via-secondary to-tertiary text-white shadow-md glow-primary">
          <ZapIcon className="h-5 w-5 fill-current" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-primary bg-clip-text text-transparent font-heading">
            FlowPilot AI
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">Autonomous Workforce OS</span>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-3.5 space-y-4">
        {sidebarSections.map((group) => (
          <div key={group.category} className="space-y-1">
            <h4 className="px-3 text-[9px] font-bold text-muted-foreground uppercase tracking-widest font-mono">
              {group.category}
            </h4>
            <nav className="mt-1 space-y-0.5">
              {group.items.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={onMobileNavigate}
                    className={cn(
                      "flex items-center justify-between px-3 py-1.5 text-xs font-medium rounded-xl transition-all duration-150 group",
                      isActive
                        ? "bg-primary/15 text-primary font-semibold border border-primary/25 shadow-sm"
                        : "text-muted-foreground hover:text-foreground hover:bg-surface-high/60"
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      <span className={cn("transition-transform group-hover:scale-110", isActive && "scale-110")}>
                        {item.icon}
                      </span>
                      <span>{item.name}</span>
                    </div>

                    {item.badge ? (
                      <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold rounded-md bg-secondary/20 text-secondary border border-secondary/30">
                        {item.badge}
                      </span>
                    ) : (
                      <ChevronRight className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* Footer Controls & System Status */}
      <div className="p-3 border-t border-border/60 bg-surface/30 space-y-2">
        <button
          onClick={() => {
            openStudio();
            onMobileNavigate?.();
          }}
          className="flex w-full items-center justify-between px-3 py-2 rounded-xl bg-primary/10 hover:bg-primary/20 border border-primary/30 text-primary transition-all text-xs font-semibold"
        >
          <div className="flex items-center gap-2">
            <Palette className="h-3.5 w-3.5" />
            <span>Appearance Studio</span>
          </div>
          <span className="text-[10px] font-mono uppercase bg-primary/20 px-1.5 py-0.5 rounded text-primary">
            {themeConfig.preset}
          </span>
        </button>

        <div className="flex items-center justify-between p-2 rounded-xl bg-surface-container/60 border border-border/40 text-[11px] font-mono">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-muted-foreground">Fleet Active</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-semibold">12/12 Ready</span>
        </div>
      </div>
    </aside>
  );
};
