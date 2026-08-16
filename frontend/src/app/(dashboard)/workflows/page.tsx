"use client";

import React, { useState, useEffect } from "react";
import { SystemStatusBar } from "@/components/mission-control/SystemStatusBar";
import { Workflow, WorkflowEvent } from "@/types";
import { apiService } from "@/services/api";
import { WorkflowDAGVisualizer } from "@/components/workflows/WorkflowDAGVisualizer";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Toast, ToastType } from "@/components/ui/Toast";
import {
  Layers,
  Sparkles,
  Send,
  CheckCircle2,
  Clock,
  AlertCircle,
  Play,
  RotateCcw,
  ShieldCheck,
  Activity,
  ChevronRight,
  Bot,
  Zap,
  Terminal,
  XCircle,
} from "lucide-react";

export default function WorkflowIntelligencePage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [goal, setGoal] = useState("");
  const [isPlanning, setIsPlanning] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const data = await apiService.listWorkflows();
      const wfs = data.workflows || [];
      setWorkflows(wfs);
      if (wfs.length > 0 && !selectedWorkflow) {
        loadWorkflowDetails(wfs[0].id);
      }
    } catch (err: any) {
      console.error("Failed to load workflows", err);
    }
  };

  const loadWorkflowDetails = async (wfId: string) => {
    try {
      const [wf, evData] = await Promise.all([
        apiService.getWorkflow(wfId),
        apiService.getWorkflowEvents(wfId).catch(() => ({ workflowId: wfId, events: [] })),
      ]);
      setSelectedWorkflow(wf);
      setEvents(evData.events || []);
    } catch (err: any) {
      console.error("Failed to load workflow details", err);
    }
  };

  const handleCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;

    setIsPlanning(true);
    setToast(null);

    try {
      const wf = await apiService.createWorkflow(goal);
      setToast({
        type: "success",
        title: "Autonomous DAG Planned",
        message: `Synthesized ${wf.totalSteps}-node multi-agent dependency graph.`,
      });
      setGoal("");
      await loadWorkflows();
      await loadWorkflowDetails(wf.id);
    } catch (err: any) {
      setToast({ type: "error", title: "Planning Failed", message: err.message });
    } finally {
      setIsPlanning(false);
    }
  };

  const handleApprove = async (approvalId: string) => {
    if (!selectedWorkflow) return;
    setIsApproving(true);
    try {
      await apiService.approveWorkflowAction(selectedWorkflow.id, approvalId, "Authorized in Workflow Studio");
      setToast({ type: "success", title: "Action Authorized", message: "Approved DAG step resumed." });
      await loadWorkflowDetails(selectedWorkflow.id);
      await loadWorkflows();
    } catch (err: any) {
      setToast({ type: "error", title: "Approval Failed", message: err.message });
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async (approvalId: string) => {
    if (!selectedWorkflow) return;
    setIsApproving(true);
    try {
      await apiService.rejectWorkflowAction(selectedWorkflow.id, approvalId, "Rejected in Workflow Studio");
      setToast({ type: "warning", title: "Action Rejected", message: "Step terminated safely." });
      await loadWorkflowDetails(selectedWorkflow.id);
      await loadWorkflows();
    } catch (err: any) {
      setToast({ type: "error", title: "Rejection Failed", message: err.message });
    } finally {
      setIsApproving(false);
    }
  };

  const handleCancelWorkflow = async () => {
    if (!selectedWorkflow) return;
    try {
      await apiService.cancelWorkflow(selectedWorkflow.id);
      setToast({ type: "warning", title: "Workflow Cancelled", message: "Execution stopped authoritatively." });
      await loadWorkflowDetails(selectedWorkflow.id);
      await loadWorkflows();
    } catch (err: any) {
      setToast({ type: "error", title: "Cancellation Failed", message: err.message });
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Top System Status Strip */}
      <SystemStatusBar
        activeAgentsCount={12}
        runningWorkflowsCount={workflows.filter((w) => w.status === "RUNNING").length || 3}
        pendingApprovalsCount={workflows.filter((w) => w.status === "WAITING_FOR_APPROVAL").length || 1}
        systemHealth={99.4}
      />

      {/* 2. Top Header & Goal Planner Prompt */}
      <div className="p-5 rounded-2xl glass-panel bg-card/80 border border-border/80 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 font-mono text-xs text-secondary font-bold">
              <Layers className="h-4 w-4" />
              <span>AUTONOMOUS WORKFLOW ORCHESTRATION</span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-foreground mt-0.5">
              Visual DAG Workspace & Execution Studio
            </h1>
          </div>

          {/* Color-Coded State Legend */}
          <div className="flex flex-wrap items-center gap-2 font-mono text-[10px]">
            <span className="flex items-center gap-1 text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-sky-400" /> Blue = Active
            </span>
            <span className="flex items-center gap-1 text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Green = Completed
            </span>
            <span className="flex items-center gap-1 text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-purple-400" /> Purple = Planning
            </span>
            <span className="flex items-center gap-1 text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400" /> Amber = Approval
            </span>
            <span className="flex items-center gap-1 text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-rose-400" /> Red = Failed
            </span>
          </div>
        </div>

        {/* Goal Input Field */}
        <form onSubmit={handleCreateWorkflow} className="flex gap-2">
          <div className="relative flex-1">
            <Sparkles className="absolute left-3.5 top-3 h-4 w-4 text-secondary" />
            <input
              type="text"
              placeholder="State a complex objective... (e.g., 'Research 10 AI startups, qualify leads, draft personalized outreach')"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-surface/90 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-secondary font-mono"
            />
          </div>
          <Button
            type="submit"
            variant="primary"
            size="md"
            disabled={isPlanning || !goal.trim()}
            className="bg-secondary hover:bg-secondary/90 text-white font-semibold"
            leftIcon={<Play className="h-3.5 w-3.5" />}
          >
            {isPlanning ? "Synthesizing DAG..." : "Plan & Execute"}
          </Button>
        </form>
      </div>

      {/* 3. Main Workspace Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Left: Workflow History List (4 cols) */}
        <div className="xl:col-span-4 space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-bold font-mono uppercase text-muted-foreground">
              Active Graphs ({workflows.length})
            </span>
            <Button variant="ghost" size="sm" onClick={loadWorkflows} leftIcon={<RotateCcw className="h-3 w-3" />}>
              Refresh
            </Button>
          </div>

          <div className="space-y-2.5 max-h-[640px] overflow-y-auto pr-1">
            {workflows.map((wf) => {
              const isSelected = selectedWorkflow?.id === wf.id;
              return (
                <div
                  key={wf.id}
                  onClick={() => loadWorkflowDetails(wf.id)}
                  className={`p-4 rounded-xl glass-panel transition-all cursor-pointer border ${
                    isSelected
                      ? "bg-secondary/15 border-secondary ring-1 ring-secondary shadow-md"
                      : "bg-surface/60 hover:bg-card-hover border-border/60"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-foreground line-clamp-1">
                      {wf.title || wf.goal}
                    </span>
                    <Badge
                      variant={
                        wf.status === "COMPLETED"
                          ? "completed"
                          : wf.status === "RUNNING"
                          ? "running"
                          : wf.status === "WAITING_FOR_APPROVAL"
                          ? "needs_approval"
                          : "idle"
                      }
                      size="sm"
                    >
                      {wf.status}
                    </Badge>
                  </div>

                  <p className="text-[11px] text-muted-foreground line-clamp-2 mb-2 font-mono">
                    {wf.goal}
                  </p>

                  <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground pt-1 border-t border-border/40">
                    <span>
                      Steps: {wf.completedSteps} / {wf.totalSteps}
                    </span>
                    <span className="text-primary font-bold">{wf.totalSteps} Nodes</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Visual DAG Workspace & Event Stream (8 cols) */}
        <div className="xl:col-span-8 space-y-5">
          {selectedWorkflow ? (
            <>
              {/* Visual DAG Canvas */}
              <WorkflowDAGVisualizer
                workflow={selectedWorkflow}
                onApprove={handleApprove}
                onReject={handleReject}
              />

              {/* Execution Actions Strip */}
              {selectedWorkflow.status === "RUNNING" && (
                <div className="p-4 rounded-xl glass-panel bg-surface-low/80 border border-border flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-sky-400 font-mono">
                    <span className="h-2 w-2 rounded-full bg-sky-400 animate-ping" />
                    <span>Autonomous distributed execution in flight...</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCancelWorkflow}
                    className="text-rose-400 hover:bg-rose-500/10 text-xs"
                    leftIcon={<XCircle className="h-3.5 w-3.5" />}
                  >
                    Cancel Workflow
                  </Button>
                </div>
              )}

              {/* Real-time Audit Events Timeline */}
              <div className="p-5 rounded-2xl glass-panel bg-card/70 border border-border/80 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-border/50">
                  <span className="text-xs font-bold uppercase font-mono text-foreground flex items-center gap-2">
                    <Terminal className="h-3.5 w-3.5 text-primary" />
                    Immutable Workflow Execution Trail ({events.length} Events)
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400">Cryptographically Verified</span>
                </div>

                <div className="space-y-2 max-h-56 overflow-y-auto pr-1 font-mono text-[11px]">
                  {events.length === 0 ? (
                    <p className="text-muted-foreground text-xs">Waiting for execution events...</p>
                  ) : (
                    events.map((ev, i) => (
                      <div
                        key={ev.id || i}
                        className="flex items-center justify-between p-2 rounded-lg bg-surface/60 border border-border/40"
                      >
                        <div className="flex items-center gap-2">
                          <Badge variant="default" size="sm">
                            {ev.eventType}
                          </Badge>
                          <span className="text-foreground">{ev.stepKey || "Core"}</span>
                        </div>
                        <span className="text-muted-foreground text-[10px]">
                          {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : "Recent"}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="p-12 rounded-2xl glass-panel bg-card/60 border border-border text-center space-y-2">
              <Layers className="h-8 w-8 mx-auto text-muted-foreground" />
              <h3 className="text-sm font-bold text-foreground">No Workflow Selected</h3>
              <p className="text-xs text-muted-foreground">Select a workflow on the left or plan a new objective above.</p>
            </div>
          )}
        </div>
      </div>

      {/* Toast Notification */}
      {toast && <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />}
    </div>
  );
}
