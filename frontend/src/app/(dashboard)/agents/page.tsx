"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Toast, ToastType } from "@/components/ui/Toast";
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
  ShieldAlert,
  Sliders,
  Check
} from "lucide-react";

interface AgentItem {
  name: string;
  description: string;
  systemPolicy: string;
  allowedTools: string[];
  deniedTools: string[];
  memoryPolicy: string;
  status: string;
  successRate: number;
  avgLatencyMs: number;
  recentRuns: number;
}

export default function AgentsHubPage() {
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentItem | null>(null);
  const [isRunModalOpen, setIsRunModalOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState<any>(null);

  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/agents", {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setAgents(data.agents || []);
      }
    } catch (err) {
      console.error("Failed to load agents", err);
    }
  };

  const handleOpenRunModal = (agent: AgentItem) => {
    setSelectedAgent(agent);
    setPrompt(`Execute priority task for ${agent.name}`);
    setRunResult(null);
    setIsRunModalOpen(true);
  };

  const handleRunAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || !selectedAgent) return;

    setIsRunning(true);
    setRunResult(null);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/agents/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          query: prompt,
          agentName: selectedAgent.name,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Agent execution error.");
      }

      const data = await res.json();
      setRunResult(data);
      setToast({ type: "success", title: "Execution Complete", message: `Agent '${data.agentName}' finished task.` });
    } catch (err: any) {
      setToast({ type: "error", title: "Execution Error", message: err.message });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Bot className="h-6 w-6 text-indigo-400" />
            AI Multi-Agent Ecosystem
          </h1>
          <p className="text-xs text-muted-foreground">
            10 specialized AI agents with explicit ALLOW/DENY permissions, scoped memory, and human-in-the-loop approvals.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="completed" className="font-mono text-xs">
            <Zap className="h-3 w-3 mr-1 text-emerald-400" />
            10 Active Agents Online
          </Badge>
        </div>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <Card key={agent.name} glass className="p-5 flex flex-col justify-between space-y-4 hover:border-indigo-500/40 transition-all">
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center font-bold shadow-md">
                    <Bot className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-foreground">{agent.name}</h3>
                    <span className="text-[10px] text-emerald-400 font-mono font-semibold">{agent.successRate}% Success Rate</span>
                  </div>
                </div>

                <Badge variant="completed" className="text-[10px] font-mono">
                  {agent.status.toUpperCase()}
                </Badge>
              </div>

              <p className="text-xs text-muted-foreground line-clamp-2">{agent.description}</p>

              {/* Permissions List */}
              <div className="space-y-2 pt-2 border-t border-border/40 text-[11px]">
                <div>
                  <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider block mb-1">
                    Allowed Tools ({agent.allowedTools.length})
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {agent.allowedTools.map((t) => (
                      <span key={t} className="px-1.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-mono text-[9px]">
                        ✓ {t}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="text-[10px] font-semibold text-rose-400 uppercase tracking-wider block mb-1">
                    Denied Permissions ({agent.deniedTools.length})
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {agent.deniedTools.map((d) => (
                      <span key={d} className="px-1.5 py-0.5 rounded-md bg-rose-500/10 text-rose-300 border border-rose-500/20 font-mono text-[9px]">
                        ✕ {d}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-border/50 flex items-center justify-between">
              <div className="flex items-center gap-3 text-[10px] font-mono text-muted-foreground">
                <span>{agent.avgLatencyMs}ms avg</span>
                <span>•</span>
                <span>{agent.recentRuns} Runs</span>
              </div>

              <Button variant="primary" size="sm" onClick={() => handleOpenRunModal(agent)} leftIcon={<Play className="h-3 w-3" />}>
                Run Agent
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {/* RUN AGENT MODAL */}
      {selectedAgent && (
        <Modal
          isOpen={isRunModalOpen}
          onClose={() => setIsRunModalOpen(false)}
          title={`Dispatch Task to ${selectedAgent.name}`}
        >
          <form onSubmit={handleRunAgent} className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-secondary/30 border border-border/60 space-y-1">
              <span className="font-semibold text-foreground block">{selectedAgent.name} System Policy</span>
              <p className="text-[11px] text-muted-foreground">{selectedAgent.systemPolicy}</p>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-foreground">Task Prompt / Query</label>
              <textarea
                rows={3}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="w-full rounded-xl glass-panel bg-secondary/40 p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 resize-none"
              />
            </div>

            {runResult && (
              <div className="p-4 rounded-xl glass-panel bg-secondary/50 border border-indigo-500/30 space-y-3 font-mono">
                <div className="flex items-center justify-between">
                  <span className="text-indigo-300 font-bold">Execution Output</span>
                  <Badge variant={runResult.status === "needs_approval" ? "failed" : "completed"}>
                    {runResult.status}
                  </Badge>
                </div>

                <p className="text-slate-200 text-xs whitespace-pre-wrap">{runResult.outputText}</p>

                <div className="pt-2 border-t border-border/40 text-[10px] space-y-1">
                  <span className="text-muted-foreground block">Safe Execution Reasoning:</span>
                  <p className="text-purple-300 italic">{runResult.reasoningSummary}</p>
                </div>

                {runResult.requiresApproval && (
                  <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 space-y-2">
                    <span className="font-bold flex items-center gap-1 text-[11px]">
                      <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                      Human Approval Required
                    </span>
                    <p className="text-[10px]">{runResult.actionToApprove}</p>
                    <Link
                      href={`/agents/runs/${runResult.runId}`}
                      className="inline-flex items-center text-[10px] font-bold text-amber-400 underline hover:text-amber-200"
                    >
                      Open Run Detail & Approve <ArrowRight className="h-3 w-3 ml-1" />
                    </Link>
                  </div>
                )}
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" type="button" onClick={() => setIsRunModalOpen(false)}>
                Close
              </Button>
              <Button variant="primary" size="sm" type="submit" isLoading={isRunning} rightIcon={<Send className="h-3 w-3" />}>
                Execute Agent
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
