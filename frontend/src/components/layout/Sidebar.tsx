"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
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
  Terminal,
  Activity
} from "lucide-react";

export const navCategories = [
  {
    category: "AI Orchestration",
    items: [
      { name: "Command Center", href: "/command-center", icon: <Sparkles className="h-4 w-4 text-primary" />, badge: "AI" },
      { name: "Workflow Intelligence", href: "/workflows", icon: <Layers className="h-4 w-4 text-secondary" />, badge: "DAG" },
      { name: "AI Agents (12)", href: "/agents", icon: <Bot className="h-4 w-4 text-indigo-400" />, badge: "12 Live" },
      { name: "Human Approvals", href: "/approvals", icon: <ShieldCheck className="h-4 w-4 text-amber-400" />, badge: "Gate" },
      { name: "AI Observability", href: "/analytics", icon: <Activity className="h-4 w-4 text-tertiary" /> },
    ],
  },
  {
    category: "CRM & Growth",
    items: [
      { name: "Lead Intelligence", href: "/leads", icon: <Users className="h-4 w-4 text-emerald-400" /> },
      { name: "Personalized Outreach", href: "/outreach", icon: <Send className="h-4 w-4 text-primary" /> },
      { name: "Follow-up Cadences", href: "/follow-ups", icon: <Clock className="h-4 w-4 text-rose-400" /> },
      { name: "Client CRM", href: "/clients", icon: <UserCheck className="h-4 w-4 text-tertiary" /> },
    ],
  },
  {
    category: "Workplace & Execution",
    items: [
      { name: "Projects & Scopes", href: "/projects", icon: <Briefcase className="h-4 w-4 text-sky-400" /> },
      { name: "Focus & Tasks", href: "/tasks", icon: <CheckSquare className="h-4 w-4 text-amber-400" /> },
      { name: "Knowledge Vault", href: "/knowledge", icon: <BookOpen className="h-4 w-4 text-secondary" /> },
      { name: "Skill Accelerator", href: "/learning", icon: <GraduationCap className="h-4 w-4 text-emerald-400" /> },
    ],
  },
  {
    category: "Security & Governance",
    items: [
      { name: "Trust & Security", href: "/security", icon: <Shield className="h-4 w-4 text-rose-400" /> },
      { name: "Automations", href: "/automations", icon: <Zap className="h-4 w-4 text-amber-400" /> },
      { name: "Integrations", href: "/integrations", icon: <Layers className="h-4 w-4 text-slate-400" /> },
      { name: "Settings", href: "/settings", icon: <Settings className="h-4 w-4 text-slate-400" /> },
    ],
  },
];

export interface SidebarProps {
  className?: string;
  onMobileNavigate?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ className, onMobileNavigate }) => {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "flex flex-col h-full w-64 glass-panel bg-surface-lowest/95 border-r border-border/80 text-foreground overflow-hidden select-none shrink-0 z-20",
        className
      )}
    >
      {/* Brand Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-border/60 bg-surface/50">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-primary via-secondary to-tertiary text-white shadow-glow-blue">
          <ZapIcon className="h-5 w-5 fill-current" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-primary bg-clip-text text-transparent font-heading">
            FlowPilot AI
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">Multi-Agent Orchestrator</span>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {navCategories.map((group) => (
          <div key={group.category} className="space-y-1">
            <h4 className="px-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-widest font-mono">
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
                      "flex items-center justify-between px-3 py-2 text-xs font-medium rounded-xl transition-all duration-150 group",
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

      {/* System Status Footer */}
      <div className="p-3 border-t border-border/60 bg-surface/30">
        <div className="flex items-center justify-between p-2.5 rounded-xl bg-surface-container/60 border border-border/40 text-[11px]">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-muted-foreground font-medium">12 Agents Active</span>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 font-semibold">Ready</span>
        </div>
      </div>
    </aside>
  );
};
