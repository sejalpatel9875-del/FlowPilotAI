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
  ShieldCheck
} from "lucide-react";

interface AgentItem {
  name: string;
  description: string;
  purpose: string;
  riskLevel: string;
  status: string;
  totalRuns: number;
  avgLatencyMs: number;
  allowedDataScopes: string[];
  allowedTools: string[];
}

interface AgentRun {
  id: string;
  agentName: string;
  requestId?: string;
  inputSummary: string;
  status: string;
  startedAt?: string;
  completedAt?: string;
  latencyMs: number;
  outputSummary?: string;
}

export default function AgentsHubPage() {
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentItem | null>(null);
  const [isRunModalOpen, setIsRunModalOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState<any>(null);

  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchDashboard();
    fetchRuns();
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/agents/dashboard", { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setAgents(data.agents || []);
      }
    } catch (err) {
      console.error("Failed to load agent dashboard", err);
    }
  };

  const fetchRuns = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/agents/runs", { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setRuns(data.runs || []);
      }
    } catch (err) {
      console.error("Failed to load agent runs", err);
    }
  };

  const handleOpenRunModal = (agent: AgentItem) => {
    setSelectedAgent(agent);
    setPrompt(`Execute task for ${agent.name}`);
    setRunResult(null);
    setIsRunModalOpen(true);
  };

  const handleRunAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsRunning(true);
    setRunResult(null);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/agents/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ prompt: prompt }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Agent execution failed.");
      }

      const data = await res.json();
      setRunResult(data);
      setToast({ type: "success", title: "Task Executed", message: `Orchestrator finished query using ${data.agentsExecuted?.join(", ")}.` });
      fetchRuns();
      fetchDashboard();
    } catch (err: any) {
      setToast({ type: "error", title: "Execution Failed", message: err.message });
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
            Production Multi-Agent Orchestrator
          </h1>
          <p className="text-xs text-muted-foreground">
            9 specialized AI agents powered by NVIDIA Nemotron 3 Ultra with strict tenant data isolation & prompt injection defense.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="completed" className="font-mono text-xs">
            <Zap className="h-3 w-3 mr-1 text-emerald-400" />
            9 Agents Active & Ready
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
                    <span className="text-[10px] text-muted-foreground font-mono">{agent.purpose}</span>
                  </div>
                </div>

                <Badge
                  variant={agent.riskLevel === "HIGH" ? "failed" : agent.riskLevel === "MEDIUM" ? "warning" : "completed"}
                  className="text-[10px] font-mono"
                >
                  {agent.riskLevel} RISK
                </Badge>
              </div>

              <p className="text-xs text-muted-foreground line-clamp-2">{agent.description}</p>

              {/* Data Scopes */}
              <div className="space-y-1.5 pt-2 border-t border-border/40 text-[11px]">
                <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider block">
                  Allowed Data Scopes
                </span>
                <div className="flex flex-wrap gap-1">
                  {agent.allowedDataScopes.map((s) => (
                    <span key={s} className="px-1.5 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono text-[9px]">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-border/50 flex items-center justify-between">
              <div className="flex items-center gap-3 text-[10px] font-mono text-muted-foreground">
                <span>{agent.avgLatencyMs}ms avg</span>
                <span>•</span>
                <span>{agent.totalRuns} Runs</span>
              </div>

              <Button variant="primary" size="sm" onClick={() => handleOpenRunModal(agent)} leftIcon={<Play className="h-3 w-3" />}>
                Execute Task
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {/* Recent Agent Runs Table */}
      <Card glass className="p-5 space-y-4">
        <CardHeader className="p-0 pb-3 border-b border-border/60">
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="h-4 w-4 text-emerald-400" />
            Recent Agent Execution History
          </CardTitle>
          <CardDescription>Real-time audit log of multi-agent runs</CardDescription>
        </CardHeader>

        <CardContent className="p-0 pt-2">
          {runs.length === 0 ? (
            <p className="text-xs text-muted-foreground py-4 text-center">No agent runs executed yet. Dispatch a task above.</p>
          ) : (
            <div className="space-y-2">
              {runs.map((r) => (
                <div key={r.id} className="p-3 rounded-xl glass-panel bg-secondary/30 border border-border/60 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-indigo-300 font-mono">{r.agentName}</span>
                    <span className="text-muted-foreground max-w-xs truncate">{r.inputSummary}</span>
                  </div>

                  <div className="flex items-center gap-4 text-right">
                    <Badge variant={r.status === "needs_approval" ? "needs_approval" : r.status === "failed" ? "failed" : "completed"}>
                      {r.status.toUpperCase()}
                    </Badge>
                    <span className="font-mono text-[10px] text-muted-foreground">{r.latencyMs}ms</span>
                    <Link href={`/agents/runs/${r.id}`} className="text-indigo-400 hover:underline text-[11px] font-semibold">
                      View Details
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* RUN AGENT MODAL */}
      {selectedAgent && (
        <Modal
          isOpen={isRunModalOpen}
          onClose={() => setIsRunModalOpen(false)}
          title={`Dispatch Task to ${selectedAgent.name}`}
        >
          <form onSubmit={handleRunAgent} className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-secondary/30 border border-border/60 space-y-1">
              <span className="font-semibold text-foreground block">{selectedAgent.name} Scope</span>
              <p className="text-[11px] text-muted-foreground">{selectedAgent.description}</p>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-foreground">Task Prompt</label>
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
                  <span className="text-indigo-300 font-bold">Orchestrator Output</span>
                  <Badge variant="completed">EXECUTED ({runResult.totalLatencyMs}ms)</Badge>
                </div>

                <p className="text-slate-200 text-xs whitespace-pre-wrap">{runResult.finalResponse}</p>
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" type="button" onClick={() => setIsRunModalOpen(false)}>
                Close
              </Button>
              <Button variant="primary" size="sm" type="submit" isLoading={isRunning} rightIcon={<Send className="h-3 w-3" />}>
                Execute Task
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
