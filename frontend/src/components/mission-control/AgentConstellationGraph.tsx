"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, Bot, Zap, Activity, ShieldCheck, ArrowUpRight, Cpu } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

export interface AgentNodeData {
  name: string;
  role: string;
  status: "idle" | "executing" | "waiting" | "completed" | "warning" | "failed";
  currentTask: string;
  confidence: number;
  latencyMs: number;
  tokenUsage: string;
  category: "Growth" | "Intelligence" | "Operations" | "Execution";
}

export const FLEET_AGENTS: AgentNodeData[] = [
  {
    name: "LeadAgent",
    role: "Lead Scoring & CRM Qualification",
    status: "executing",
    currentTask: "Scoring 14 enterprise inbound prospects",
    confidence: 96,
    latencyMs: 340,
    tokenUsage: "48.2k",
    category: "Growth",
  },
  {
    name: "ResearchAgent",
    role: "Market & Account Intelligence",
    status: "executing",
    currentTask: "Deep scraping AI SaaS competitive landscape",
    confidence: 94,
    latencyMs: 820,
    tokenUsage: "112.5k",
    category: "Intelligence",
  },
  {
    name: "OutreachAgent",
    role: "Personalized Campaign Dispatcher",
    status: "waiting",
    currentTask: "Waiting for human approval on Tier-1 sequence",
    confidence: 91,
    latencyMs: 410,
    tokenUsage: "34.1k",
    category: "Growth",
  },
  {
    name: "FollowUpAgent",
    role: "Cadence & Escalation Engine",
    status: "idle",
    currentTask: "Monitoring 42 active lead conversations",
    confidence: 98,
    latencyMs: 190,
    tokenUsage: "18.7k",
    category: "Growth",
  },
  {
    name: "ProposalAgent",
    role: "Scope & SOW Architect",
    status: "idle",
    currentTask: "Ready for statement of work generation",
    confidence: 95,
    latencyMs: 510,
    tokenUsage: "62.4k",
    category: "Execution",
  },
  {
    name: "ProjectAgent",
    role: "Milestone & Sprint Coordinator",
    status: "completed",
    currentTask: "Updated Q3 enterprise sprint deliverables",
    confidence: 99,
    latencyMs: 280,
    tokenUsage: "29.8k",
    category: "Execution",
  },
  {
    name: "AnalyticsAgent",
    role: "Revenue & Fleet Telemetry",
    status: "idle",
    currentTask: "Aggregating weekly conversion metrics",
    confidence: 97,
    latencyMs: 240,
    tokenUsage: "45.0k",
    category: "Intelligence",
  },
  {
    name: "LearningAgent",
    role: "Skill & Model Optimization",
    status: "idle",
    currentTask: "Tuning prompt heuristics from rejected outputs",
    confidence: 92,
    latencyMs: 650,
    tokenUsage: "88.3k",
    category: "Intelligence",
  },
  {
    name: "TimeManagementAgent",
    role: "Focus & Schedule Optimizer",
    status: "idle",
    currentTask: "Synchronizing high-priority focus calendar",
    confidence: 98,
    latencyMs: 150,
    tokenUsage: "14.2k",
    category: "Operations",
  },
  {
    name: "InvitationAgent",
    role: "Discovery Call & Meeting Planner",
    status: "idle",
    currentTask: "Coordinating 3 executive stakeholder calls",
    confidence: 96,
    latencyMs: 310,
    tokenUsage: "22.6k",
    category: "Operations",
  },
  {
    name: "LocationTracerAgent",
    role: "Timezone & Geo Intelligence",
    status: "idle",
    currentTask: "Resolving timezone clusters across EMEA & APAC",
    confidence: 99,
    latencyMs: 120,
    tokenUsage: "9.4k",
    category: "Intelligence",
  },
  {
    name: "ReminderAgent",
    role: "Proactive Deadline Guardian",
    status: "idle",
    currentTask: "Tracking 8 milestone delivery deadlines",
    confidence: 99,
    latencyMs: 110,
    tokenUsage: "11.8k",
    category: "Operations",
  },
];

export interface AgentConstellationGraphProps {
  onSelectAgent?: (agent: AgentNodeData) => void;
  selectedAgentName?: string | null;
  className?: string;
}

export const AgentConstellationGraph: React.FC<AgentConstellationGraphProps> = ({
  onSelectAgent,
  selectedAgentName,
  className = "",
}) => {
  const [activePulse, setActivePulse] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActivePulse((p) => (p + 1) % FLEET_AGENTS.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: AgentNodeData["status"]) => {
    switch (status) {
      case "executing":
        return {
          bg: "bg-primary/20",
          border: "border-primary",
          text: "text-primary",
          dot: "bg-primary animate-ping",
          glow: "0 0 20px rgba(46, 123, 255, 0.4)",
        };
      case "waiting":
        return {
          bg: "bg-amber-500/20",
          border: "border-amber-500",
          text: "text-amber-400",
          dot: "bg-amber-500",
          glow: "0 0 20px rgba(245, 158, 11, 0.35)",
        };
      case "completed":
        return {
          bg: "bg-emerald-500/20",
          border: "border-emerald-500",
          text: "text-emerald-400",
          dot: "bg-emerald-500",
          glow: "0 0 15px rgba(16, 185, 129, 0.3)",
        };
      case "failed":
        return {
          bg: "bg-rose-500/20",
          border: "border-rose-500",
          text: "text-rose-400",
          dot: "bg-rose-500",
          glow: "0 0 20px rgba(244, 63, 94, 0.4)",
        };
      default:
        return {
          bg: "bg-surface-high/60",
          border: "border-border/80",
          text: "text-muted-foreground",
          dot: "bg-slate-400",
          glow: "none",
        };
    }
  };

  return (
    <div
      className={`relative flex flex-col items-center justify-center min-h-[480px] w-full rounded-2xl glass-panel p-6 overflow-hidden select-none border border-border/80 bg-card/60 ${className}`}
    >
      {/* Background Orbital Rings & Radar Mesh */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-40">
        <div className="absolute h-[420px] w-[420px] rounded-full border border-primary/20 animate-[spin_60s_linear_infinite]" />
        <div className="absolute h-[290px] w-[290px] rounded-full border border-border/40 border-dashed animate-[spin_40s_linear_infinite_reverse]" />
        <div className="absolute h-[160px] w-[160px] rounded-full border border-ai-core-color/30" />
      </div>

      {/* Top Banner Tag */}
      <div className="absolute top-4 left-5 flex items-center gap-2 font-mono text-[11px] text-muted-foreground z-10">
        <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
        <span className="uppercase tracking-widest text-foreground font-bold">
          Autonomous Fleet Constellation
        </span>
        <span className="text-muted-foreground">| 12 Intelligent Nodes</span>
      </div>

      {/* Center Core: FLOWPILOT AI CORE */}
      <div className="relative z-10 flex flex-col items-center justify-center my-4 group cursor-pointer">
        <div
          className="relative flex h-24 w-24 items-center justify-center rounded-full glass-panel border-2 border-ai-core-color shadow-2xl transition-transform duration-300 group-hover:scale-105"
          style={{
            backgroundColor: "rgba(17, 19, 24, 0.85)",
            boxShadow: "0 0 40px var(--ai-core-glow)",
          }}
        >
          {/* Inner pulsating core */}
          <div
            className="h-12 w-12 rounded-full flex items-center justify-center text-black font-bold shadow-inner ai-core-pulse"
            style={{ backgroundColor: "var(--ai-core-color)" }}
          >
            <Sparkles className="h-6 w-6" />
          </div>
        </div>

        <div className="mt-2 text-center">
          <div className="text-xs font-bold tracking-wider uppercase font-mono text-foreground">
            FlowPilot Core
          </div>
          <div className="text-[10px] font-mono text-primary flex items-center justify-center gap-1">
            <Cpu className="h-2.5 w-2.5" />
            <span>NVIDIA Nemotron 3 Ultra</span>
          </div>
        </div>
      </div>

      {/* 12 Outer Agent Nodes Grid / Constellation */}
      <div className="relative z-10 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3 w-full mt-4">
        {FLEET_AGENTS.map((agent, index) => {
          const style = getStatusColor(agent.status);
          const isSelected = selectedAgentName === agent.name;
          const isPulsing = activePulse === index;

          return (
            <div
              key={agent.name}
              onClick={() => onSelectAgent?.(agent)}
              className={`relative flex flex-col justify-between p-3 rounded-xl glass-panel transition-all duration-200 cursor-pointer border ${
                isSelected
                  ? "bg-primary/15 border-primary ring-1 ring-primary shadow-lg"
                  : isPulsing
                  ? "border-primary/60 bg-surface-high/90 shadow-md"
                  : "bg-surface/70 hover:bg-card-hover border-border/70 hover:border-border"
              }`}
              style={{ boxShadow: isSelected || isPulsing ? style.glow : "none" }}
            >
              {/* Header: Name + Status Dot */}
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1.5">
                  <Bot className={`h-3.5 w-3.5 ${style.text}`} />
                  <span className="text-xs font-bold tracking-tight text-foreground truncate max-w-[90px]">
                    {agent.name}
                  </span>
                </div>
                <span className={`h-2 w-2 rounded-full ${style.dot}`} />
              </div>

              {/* Current Task preview */}
              <p className="text-[10px] text-muted-foreground line-clamp-2 min-h-[26px] mb-2">
                {agent.currentTask}
              </p>

              {/* Bottom Telemetry Mini-Strip */}
              <div className="flex items-center justify-between pt-1.5 border-t border-border/40 font-mono text-[9px] text-muted-foreground">
                <span className="text-emerald-400 font-bold">{agent.confidence}% conf</span>
                <span className="text-primary font-bold">{agent.tokenUsage}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
