"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { SystemStatusBar } from "@/components/mission-control/SystemStatusBar";
import { AgentConstellationGraph, AgentNodeData, FLEET_AGENTS } from "@/components/mission-control/AgentConstellationGraph";
import { AgentInspectorDrawer } from "@/components/mission-control/AgentInspectorDrawer";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Toast, ToastType } from "@/components/ui/Toast";
import { apiService } from "@/services/api";
import {
  Bot,
  Play,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Zap,
  Shield,
  Layers,
  Search,
  Send,
  Terminal,
  Activity,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Info,
  Sliders,
  ExternalLink,
} from "lucide-react";

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentNodeData[]>(FLEET_AGENTS);
  const [selectedAgent, setSelectedAgent] = useState<AgentNodeData | null>(null);
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");

  // Run Agent Modal State
  const [runningAgentName, setRunningAgentName] = useState<string | null>(null);
  const [promptInput, setPromptInput] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any | null>(null);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  const handleOpenInspector = (agent: AgentNodeData) => {
    setSelectedAgent(agent);
    setIsInspectorOpen(true);
  };

  const handleOpenRunModal = (agentName: string) => {
    setRunningAgentName(agentName);
    setPromptInput("");
    setExecutionResult(null);
  };

  const handleExecuteAgent = async () => {
    if (!runningAgentName || !promptInput.trim()) return;

    setIsExecuting(true);
    setExecutionResult(null);

    try {
      const res = await apiService.runAgent(runningAgentName, promptInput);
      setExecutionResult(res);
      setToast({
        type: "success",
        title: `${runningAgentName} Execution Completed`,
        message: `Task completed in ${res.latencyMs || 340}ms via NVIDIA NIM Gateway.`,
      });
    } catch (err: any) {
      setToast({
        type: "error",
        title: "Execution Error",
        message: err.message || "Agent execution failed.",
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const filteredAgents = agents.filter((a) => {
    const matchesSearch =
      a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.currentTask.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCat = categoryFilter === "ALL" || a.category.toUpperCase() === categoryFilter;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="space-y-6">
      {/* 1. Top System Status Strip */}
      <SystemStatusBar
        activeAgentsCount={12}
        runningWorkflowsCount={3}
        pendingApprovalsCount={1}
        systemHealth={99.4}
      />

      {/* 2. Top Fleet Status Header Banner */}
      <div className="p-5 rounded-2xl glass-panel bg-card/80 border border-border/80 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 font-mono text-xs text-primary font-bold">
              <Bot className="h-4 w-4" />
              <span>AI FLEET CONTROL SYSTEM</span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-foreground mt-0.5">
              Specialized Autonomous Agent Fleet
            </h1>
          </div>

          {/* Status Breakdown Chips */}
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
            <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold">
              12 ACTIVE
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-surface-high border border-border text-muted-foreground">
              8 IDLE
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-primary/15 border border-primary/30 text-primary font-bold">
              2 EXECUTING
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
              1 WAITING
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400">
              1 WARNING
            </span>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border/50">
          <div className="flex items-center gap-2">
            {["ALL", "GROWTH", "INTELLIGENCE", "OPERATIONS", "EXECUTION"].map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                  categoryFilter === cat
                    ? "bg-primary text-white shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-surface-high"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search agent fleet..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-surface/80 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>
      </div>

      {/* 3. Central Interactive Constellation Canvas */}
      <AgentConstellationGraph
        selectedAgentName={selectedAgent?.name}
        onSelectAgent={handleOpenInspector}
      />

      {/* 4. Fleet Control Matrix Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredAgents.map((agent) => (
          <div
            key={agent.name}
            className="p-5 rounded-2xl glass-panel bg-card/70 border border-border/80 hover:border-primary/50 transition-all shadow-sm space-y-3.5 flex flex-col justify-between"
          >
            {/* Header */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 text-primary border border-primary/30 font-bold">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-foreground tracking-tight">{agent.name}</h3>
                    <span className="text-[10px] text-muted-foreground font-mono uppercase">{agent.category}</span>
                  </div>
                </div>

                <Badge
                  variant={
                    agent.status === "executing"
                      ? "running"
                      : agent.status === "waiting"
                      ? "warning"
                      : agent.status === "completed"
                      ? "success"
                      : "idle"
                  }
                  size="sm"
                >
                  {agent.status.toUpperCase()}
                </Badge>
              </div>

              {/* Role & Task */}
              <p className="text-xs text-foreground font-medium mb-1">{agent.role}</p>
              <div className="p-2.5 rounded-xl bg-surface/60 border border-border/40 text-[11px] text-muted-foreground font-mono leading-relaxed">
                {agent.currentTask}
              </div>
            </div>

            {/* Telemetry Row */}
            <div className="pt-2 border-t border-border/50 space-y-3 font-mono text-[11px]">
              <div className="grid grid-cols-3 gap-1 text-center">
                <div className="p-1.5 rounded-lg bg-surface-lowest/60 border border-border/30">
                  <span className="text-[9px] text-muted-foreground block">CONF</span>
                  <span className="text-emerald-400 font-bold">{agent.confidence}%</span>
                </div>
                <div className="p-1.5 rounded-lg bg-surface-lowest/60 border border-border/30">
                  <span className="text-[9px] text-muted-foreground block">TOKENS</span>
                  <span className="text-primary font-bold">{agent.tokenUsage}</span>
                </div>
                <div className="p-1.5 rounded-lg bg-surface-lowest/60 border border-border/30">
                  <span className="text-[9px] text-muted-foreground block">LATENCY</span>
                  <span className="text-sky-400 font-bold">{agent.latencyMs}ms</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <Button
                  variant="glass"
                  size="sm"
                  onClick={() => handleOpenInspector(agent)}
                  className="flex-1 justify-center text-xs"
                >
                  Inspect
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleOpenRunModal(agent.name)}
                  className="flex-1 justify-center text-xs"
                  leftIcon={<Play className="h-3 w-3" />}
                >
                  Dispatch
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 5. Slide-out Agent Inspector Drawer */}
      <AgentInspectorDrawer
        agent={selectedAgent}
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
        onRunAgent={(name) => {
          setIsInspectorOpen(false);
          handleOpenRunModal(name);
        }}
      />

      {/* 6. Dispatch Modal */}
      <Modal
        isOpen={Boolean(runningAgentName)}
        onClose={() => setRunningAgentName(null)}
        title={`Dispatch Single Agent • ${runningAgentName}`}
      >
        <div className="space-y-4 text-xs">
          <p className="text-muted-foreground">
            Execute direct domain query with isolated tenant context and sanitized prompt envelope.
          </p>

          <div className="space-y-1">
            <label className="text-xs font-bold text-foreground">Task Instruction Prompt:</label>
            <textarea
              value={promptInput}
              onChange={(e) => setPromptInput(e.target.value)}
              placeholder={`Provide instructions for ${runningAgentName}...`}
              rows={4}
              className="w-full p-3 rounded-xl bg-surface border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary font-mono"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-border">
            <Button variant="ghost" size="sm" onClick={() => setRunningAgentName(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleExecuteAgent}
              disabled={isExecuting || !promptInput.trim()}
              leftIcon={<Play className="h-3.5 w-3.5" />}
            >
              {isExecuting ? "Executing via NIM..." : "Run Agent"}
            </Button>
          </div>

          {executionResult && (
            <div className="mt-4 p-4 rounded-xl bg-surface-lowest border border-border space-y-2 font-mono text-[11px] animate-in fade-in">
              <div className="flex items-center justify-between text-emerald-400 font-bold">
                <span>EXECUTION COMPLETED</span>
                <span>{executionResult.latencyMs || 340}ms</span>
              </div>
              <pre className="p-3 rounded-lg bg-surface text-muted-foreground overflow-x-auto whitespace-pre-wrap max-h-48">
                {typeof executionResult.output === "object"
                  ? JSON.stringify(executionResult.output, null, 2)
                  : executionResult.output || JSON.stringify(executionResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </Modal>

      {/* Toast Notification */}
      {toast && <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />}
    </div>
  );
}
