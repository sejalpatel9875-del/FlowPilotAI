"use client";

import React, { useState, useEffect } from "react";
import { Workflow, WorkflowEvent } from "@/types";
import { apiService } from "@/services/api";
import { WorkflowDAGVisualizer } from "@/components/workflows/WorkflowDAGVisualizer";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
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
  ChevronRight
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
      setToast({ type: "success", title: "Workflow Planned & Initiated", message: `Generated ${wf.totalSteps}-step execution graph.` });
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
      await apiService.approveWorkflowAction(selectedWorkflow.id, approvalId, "Approved via Workflow Intelligence");
      setToast({ type: "success", title: "Action Approved", message: "Approved step execution resumed." });
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
      await apiService.rejectWorkflowAction(selectedWorkflow.id, approvalId, "Rejected via Workflow Intelligence");
      setToast({ type: "warning", title: "Action Rejected", message: "Workflow safely terminated." });
      await loadWorkflowDetails(selectedWorkflow.id);
      await loadWorkflows();
    } catch (err: any) {
      setToast({ type: "error", title: "Rejection Failed", message: err.message });
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2 font-heading">
            <Layers className="h-6 w-6 text-secondary" />
            Workflow Intelligence & DAG Orchestrator
          </h1>
          <p className="text-xs text-muted-foreground">
            Decompose natural-language business objectives into topological execution graphs with mandatory human approval gates.
          </p>
        </div>

        <Badge variant="running" className="font-mono text-xs">
          DAG Engine Active
        </Badge>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Goal Planner Input */}
      <Card glass className="p-5 border-secondary/30 bg-gradient-to-r from-surface to-surface-lowest">
        <form onSubmit={handleCreateWorkflow} className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-secondary font-heading">
            <Sparkles className="h-4 w-4" />
            <span>Create New Autonomous Multi-Agent Workflow</span>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. 'Analyze my pending leads, identify high-priority leads, draft follow-up emails, choose suitable timing, and show everything for approval'..."
              className="flex-1 w-full rounded-xl glass-panel bg-surface-lowest/90 px-4 py-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-secondary border-border/80 shadow-inner"
            />
            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isPlanning}
              disabled={!goal.trim()}
              leftIcon={<Send className="h-4 w-4" />}
              className="w-full sm:w-auto font-mono text-xs bg-secondary hover:bg-secondary/90 shadow-glow-purple"
            >
              Plan & Execute
            </Button>
          </div>
        </form>
      </Card>

      {/* Active Workflow DAG View */}
      {selectedWorkflow ? (
        <WorkflowDAGVisualizer
          workflow={selectedWorkflow}
          onApprove={handleApprove}
          onReject={handleReject}
          isApproving={isApproving}
        />
      ) : (
        <Card glass className="p-8 text-center text-xs text-muted-foreground">
          <Layers className="h-8 w-8 text-secondary/40 mx-auto mb-2" />
          No workflow selected. Create a new workflow above to view its DAG graph.
        </Card>
      )}

      {/* Workflow History & Event Trail Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Workflows List */}
        <div className="lg:col-span-2 space-y-4">
          <Card glass className="p-5 space-y-3">
            <CardHeader className="p-0 pb-2 border-b border-border/60 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-bold text-foreground font-heading">
                All Orchestrated Workflows ({workflows.length})
              </CardTitle>
              <button
                onClick={loadWorkflows}
                className="text-[11px] font-mono text-secondary hover:underline flex items-center gap-1"
              >
                <RotateCcw className="h-3 w-3" /> Refresh
              </button>
            </CardHeader>

            <CardContent className="p-0 pt-2 space-y-2">
              {workflows.length === 0 ? (
                <p className="text-xs text-muted-foreground py-4 text-center">No workflows found. Submit a goal above.</p>
              ) : (
                workflows.map((w) => (
                  <div
                    key={w.id}
                    onClick={() => loadWorkflowDetails(w.id)}
                    className={`cursor-pointer p-3.5 rounded-xl border transition-all flex items-center justify-between text-xs ${
                      selectedWorkflow?.id === w.id
                        ? "border-secondary/60 bg-secondary/15 shadow-sm"
                        : "border-border/60 bg-surface-container/40 hover:bg-surface-high"
                    }`}
                  >
                    <div className="space-y-1 max-w-md">
                      <h4 className="font-bold text-foreground line-clamp-1">{w.title || w.goal}</h4>
                      <div className="flex items-center gap-3 text-[10px] font-mono text-muted-foreground">
                        <span>{w.completedSteps}/{w.totalSteps} Steps</span>
                        <span>•</span>
                        <span>{w.createdAt ? new Date(w.createdAt).toLocaleTimeString() : ""}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <Badge
                        variant={
                          w.status === "COMPLETED"
                            ? "completed"
                            : w.status === "WAITING_FOR_APPROVAL"
                            ? "warning"
                            : w.status === "FAILED"
                            ? "failed"
                            : "running"
                        }
                        className="text-[10px] font-mono"
                      >
                        {w.status}
                      </Badge>
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Col: Immutable Audit Event Trail */}
        <div className="space-y-4">
          <Card glass className="p-5 space-y-3">
            <CardHeader className="p-0 pb-2 border-b border-border/60">
              <CardTitle className="text-sm font-bold text-foreground flex items-center gap-2 font-heading">
                <Activity className="h-4 w-4 text-tertiary" />
                Immutable Event Trail
              </CardTitle>
              <CardDescription className="text-[11px]">Audit log of DAG transitions</CardDescription>
            </CardHeader>

            <CardContent className="p-0 pt-2 space-y-2 max-h-96 overflow-y-auto font-mono text-[10px]">
              {events.length === 0 ? (
                <p className="text-muted-foreground py-4 text-center">No events for selected workflow.</p>
              ) : (
                events.map((ev) => (
                  <div key={ev.id} className="p-2.5 rounded-lg bg-surface-container/60 border border-border/40 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-tertiary font-bold">{ev.eventType}</span>
                      <span className="text-muted-foreground text-[9px]">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                    </div>
                    {ev.stepKey && <span className="text-slate-400 block">Step: {ev.stepKey}</span>}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
