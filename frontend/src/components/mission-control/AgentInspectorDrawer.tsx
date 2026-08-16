"use client";

import React, { useState } from "react";
import { Drawer } from "@/components/ui/Drawer";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { AgentNodeData } from "./AgentConstellationGraph";
import {
  Bot,
  Zap,
  Activity,
  Shield,
  Clock,
  Terminal,
  Cpu,
  Key,
  Database,
  History,
  CheckCircle2,
  AlertTriangle,
  Play,
  Copy,
  Check,
} from "lucide-react";

export interface AgentInspectorDrawerProps {
  agent: AgentNodeData | null;
  isOpen: boolean;
  onClose: () => void;
  onRunAgent?: (agentName: string) => void;
}

export const AgentInspectorDrawer: React.FC<AgentInspectorDrawerProps> = ({
  agent,
  isOpen,
  onClose,
  onRunAgent,
}) => {
  const [activeTab, setActiveTab] = useState<
    "overview" | "live_task" | "capabilities" | "tools" | "memory" | "permissions" | "telemetry" | "runs"
  >("overview");

  const [copied, setCopied] = useState(false);

  if (!agent) return null;

  const handleCopyTelemetry = () => {
    navigator.clipboard.writeText(JSON.stringify(agent, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "live_task", label: "Live Task" },
    { id: "capabilities", label: "Capabilities" },
    { id: "tools", label: "Tools" },
    { id: "memory", label: "Memory" },
    { id: "permissions", label: "Permissions" },
    { id: "telemetry", label: "Telemetry" },
    { id: "runs", label: "Recent Runs" },
  ];

  return (
    <Drawer isOpen={isOpen} onClose={onClose} position="right" title={`Agent Inspector • ${agent.name}`}>
      <div className="flex flex-col h-full space-y-5 text-foreground">
        {/* Header Strip */}
        <div className="flex items-center justify-between p-4 rounded-xl glass-panel bg-surface-low/80 border border-border/70">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15 text-primary border border-primary/30 shadow-sm">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold tracking-tight text-foreground">{agent.name}</h3>
                <Badge variant={agent.status === "executing" ? "running" : "idle"} size="sm">
                  {agent.status.toUpperCase()}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">{agent.role}</p>
            </div>
          </div>

          <Button
            variant="primary"
            size="sm"
            onClick={() => onRunAgent?.(agent.name)}
            leftIcon={<Play className="h-3.5 w-3.5" />}
          >
            Dispatch
          </Button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 border-b border-border/60 scrollbar-none">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                activeTab === tab.id
                  ? "bg-primary text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-surface-high/60"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content Panes */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1 text-xs">
          {/* 1. OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-surface/70 border border-border/60 space-y-2">
                <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold">
                  Autonomous Identity & Mission
                </span>
                <p className="text-muted-foreground leading-relaxed">
                  Specialized agent responsible for executing domain intelligence within FlowPilot's multi-agent DAG.
                  Bound to isolated tenant contexts with cryptographic secret redaction and policy-checked tools.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div className="p-3 rounded-xl bg-surface/50 border border-border/50 space-y-1">
                  <span className="text-[10px] font-mono text-muted-foreground">Category</span>
                  <div className="font-bold text-foreground capitalize">{agent.category}</div>
                </div>
                <div className="p-3 rounded-xl bg-surface/50 border border-border/50 space-y-1">
                  <span className="text-[10px] font-mono text-muted-foreground">Confidence Score</span>
                  <div className="font-bold text-emerald-400">{agent.confidence}% Standard</div>
                </div>
                <div className="p-3 rounded-xl bg-surface/50 border border-border/50 space-y-1">
                  <span className="text-[10px] font-mono text-muted-foreground">Model Gateway</span>
                  <div className="font-bold text-sky-400">NVIDIA Nemotron 3</div>
                </div>
                <div className="p-3 rounded-xl bg-surface/50 border border-border/50 space-y-1">
                  <span className="text-[10px] font-mono text-muted-foreground">Execution Latency</span>
                  <div className="font-bold text-primary font-mono">{agent.latencyMs} ms</div>
                </div>
              </div>
            </div>
          )}

          {/* 2. LIVE TASK */}
          {activeTab === "live_task" && (
            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-surface-lowest border border-border space-y-2 font-mono">
                <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                  <span>ACTIVE INSTRUCTION</span>
                  <Badge variant="running" size="sm">
                    In Flight
                  </Badge>
                </div>
                <div className="text-foreground text-xs leading-relaxed bg-surface-container/60 p-2.5 rounded-lg border border-border/40">
                  {agent.currentTask}
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-surface/50 border border-border/60 space-y-2">
                <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold">
                  Progress & Step Boundary
                </span>
                <div className="w-full bg-surface-container rounded-full h-2 overflow-hidden">
                  <div className="bg-primary h-full rounded-full transition-all duration-500" style={{ width: "72%" }} />
                </div>
                <div className="flex justify-between text-[10px] font-mono text-muted-foreground pt-1">
                  <span>Step: Context Gathering</span>
                  <span>72% Completed</span>
                </div>
              </div>
            </div>
          )}

          {/* 3. CAPABILITIES */}
          {activeTab === "capabilities" && (
            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-surface/60 border border-border/60 space-y-2">
                <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold">
                  Registered Capability Actions
                </span>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {["READ_DATABASE", "GENERATE_PLAN", "EXECUTE_TOOL", "PUBLISH_EVENT", "REQUEST_APPROVAL"].map((cap) => (
                    <span key={cap} className="px-2 py-1 rounded-md bg-surface-high border border-border font-mono text-[10px] text-foreground">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 4. TOOLS */}
          {activeTab === "tools" && (
            <div className="space-y-2.5">
              {[
                { name: "READ_LEADS", desc: "Scans tenant-scoped lead records and scoring matrix", safe: true },
                { name: "GENERATE_ANALYSIS", desc: "Performs LLM-based reasoning and data structuring", safe: true },
                { name: "DISPATCH_NOTIFICATION", desc: "Emits real-time SSE events to connected client sessions", safe: true },
              ].map((tool) => (
                <div key={tool.name} className="p-3 rounded-xl bg-surface/60 border border-border/60 space-y-1">
                  <div className="flex items-center justify-between font-mono font-bold text-foreground">
                    <span>{tool.name}</span>
                    <Badge variant="success" size="sm">
                      Policy Safe
                    </Badge>
                  </div>
                  <p className="text-[11px] text-muted-foreground">{tool.desc}</p>
                </div>
              ))}
            </div>
          )}

          {/* 5. MEMORY */}
          {activeTab === "memory" && (
            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-surface/60 border border-border/60 space-y-2 font-mono text-[11px]">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Context Window Size:</span>
                  <span className="text-foreground font-bold">32,768 tokens</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Active Memory Buffer:</span>
                  <span className="text-primary font-bold">{agent.tokenUsage}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tenant Isolation Key:</span>
                  <span className="text-emerald-400 font-bold">TENANT-ISOLATED</span>
                </div>
              </div>
            </div>
          )}

          {/* 6. PERMISSIONS */}
          {activeTab === "permissions" && (
            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-surface/60 border border-border/60 space-y-2">
                <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold">
                  Data Scope Boundaries
                </span>
                <div className="space-y-1.5 font-mono text-[11px]">
                  <div className="flex items-center gap-2 text-emerald-400">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Scoped to authenticated user workspace</span>
                  </div>
                  <div className="flex items-center gap-2 text-emerald-400">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Automatic secret & credential redaction active</span>
                  </div>
                  <div className="flex items-center gap-2 text-emerald-400">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Side-effects gated behind Human Approval Gate</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 7. TELEMETRY */}
          {activeTab === "telemetry" && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 rounded-xl bg-surface/60 border border-border/60 space-y-1">
                  <span className="text-[10px] font-mono text-muted-foreground">Total Tokens</span>
                  <div className="text-base font-bold font-mono text-primary">{agent.tokenUsage}</div>
                </div>
                <div className="p-3 rounded-xl bg-surface/60 border border-border/60 space-y-1">
                  <span className="text-[10px] font-mono text-muted-foreground">Avg Latency</span>
                  <div className="text-base font-bold font-mono text-sky-400">{agent.latencyMs} ms</div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-surface/60 border border-border/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold">
                    Raw Telemetry Payload
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCopyTelemetry}
                    leftIcon={copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                  >
                    {copied ? "Copied" : "Copy"}
                  </Button>
                </div>
                <pre className="p-2.5 rounded-lg bg-surface-lowest text-[10px] font-mono text-muted-foreground overflow-x-auto">
                  {JSON.stringify(agent, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* 8. RECENT RUNS */}
          {activeTab === "runs" && (
            <div className="space-y-2">
              {[
                { id: "run-981", time: "2 mins ago", duration: "340ms", status: "completed", summary: "Processed pipeline scoring" },
                { id: "run-980", time: "14 mins ago", duration: "410ms", status: "completed", summary: "Synchronized account records" },
                { id: "run-979", time: "1 hour ago", duration: "820ms", status: "completed", summary: "Context enrichment completed" },
              ].map((run) => (
                <div key={run.id} className="p-3 rounded-xl bg-surface/60 border border-border/60 space-y-1">
                  <div className="flex items-center justify-between font-mono text-[11px]">
                    <span className="font-bold text-foreground">{run.id}</span>
                    <span className="text-muted-foreground">{run.time}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">{run.summary}</p>
                  <div className="flex items-center justify-between pt-1 text-[10px] font-mono text-muted-foreground">
                    <span>Duration: {run.duration}</span>
                    <span className="text-emerald-400 capitalize">{run.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Drawer>
  );
};
