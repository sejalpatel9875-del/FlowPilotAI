"use client";

import React, { useState, useEffect } from "react";
import { cn } from "@/utils/cn";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { Workflow, WorkflowStatusType } from "@/types";
import { apiService } from "@/services/api";
import { WorkflowDAGVisualizer } from "@/components/workflows/WorkflowDAGVisualizer";
import { AITelemetryPanel } from "@/components/telemetry/AITelemetryPanel";
import {
  Sparkles,
  Send,
  RefreshCw,
  AlertCircle,
  Lightbulb,
  CheckCircle2,
  Bot,
  Play,
  Layers,
  Cpu
} from "lucide-react";

export interface AICommandCenterProps {
  className?: string;
  onWorkflowStateChange?: (workflow: Workflow) => void;
}

export const suggestedPrompts = [
  "Analyze my pending leads, identify high-priority leads, draft follow-up emails, choose suitable timing, and show everything to me for approval.",
  "Mere pending leads analyze karo, high-priority leads identify karo, unke liye follow-up drafts banao, suitable timing recommend karo, aur approval lo.",
  "Research market competitor strategies and generate a client proposal draft.",
  "Break down project deliverables into milestones and allocate focus blocks.",
];

export const AICommandCenter: React.FC<AICommandCenterProps> = ({ className, onWorkflowStateChange }) => {
  const [goal, setGoal] = useState("");
  const [status, setStatus] = useState<"idle" | "planning" | "running" | "waiting_approval" | "completed" | "failed">("idle");
  const [activeWorkflow, setActiveWorkflow] = useState<Workflow | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isApproving, setIsApproving] = useState(false);

  const handleDispatchGoal = async (objectiveText: string) => {
    if (!objectiveText.trim()) return;
    setGoal(objectiveText);
    setStatus("planning");
    setErrorMessage(null);
    setActiveWorkflow(null);

    try {
      // 1. Create and begin execution of multi-agent workflow
      const wf = await apiService.createWorkflow(objectiveText);
      setActiveWorkflow(wf);

      if (wf.status === "WAITING_FOR_APPROVAL") {
        setStatus("waiting_approval");
      } else if (wf.status === "COMPLETED") {
        setStatus("completed");
      } else if (wf.status === "FAILED") {
        setStatus("failed");
      } else {
        setStatus("running");
      }

      // 2. Fetch full workflow details
      const fullWf = await apiService.getWorkflow(wf.id);
      setActiveWorkflow(fullWf);
      if (onWorkflowStateChange) onWorkflowStateChange(fullWf);

      // 3. Connect real-time SSE stream for live updates
      apiService.streamWorkflow(
        wf.id,
        async (ev) => {
          if (ev.event === "state_change" || ev.event === "terminal") {
            const updatedWf = await apiService.getWorkflow(wf.id);
            setActiveWorkflow(updatedWf);
            if (updatedWf.status === "WAITING_FOR_APPROVAL") setStatus("waiting_approval");
            else if (updatedWf.status === "COMPLETED") setStatus("completed");
            else if (updatedWf.status === "FAILED") setStatus("failed");
            if (onWorkflowStateChange) onWorkflowStateChange(updatedWf);
          }
        },
        (err) => console.log("Stream connection closed or complete", err)
      );
    } catch (err: any) {
      setErrorMessage(err.message || "Multi-Agent workflow planner failed.");
      setStatus("failed");
    }
  };

  const handleApprove = async (approvalId: string) => {
    if (!activeWorkflow) return;
    setIsApproving(true);
    try {
      await apiService.approveWorkflowAction(activeWorkflow.id, approvalId, "Approved via Command Center");
      const updated = await apiService.getWorkflow(activeWorkflow.id);
      setActiveWorkflow(updated);
      setStatus(updated.status === "COMPLETED" ? "completed" : "running");
      if (onWorkflowStateChange) onWorkflowStateChange(updated);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to process approval.");
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async (approvalId: string) => {
    if (!activeWorkflow) return;
    setIsApproving(true);
    try {
      await apiService.rejectWorkflowAction(activeWorkflow.id, approvalId, "Rejected via Command Center");
      const updated = await apiService.getWorkflow(activeWorkflow.id);
      setActiveWorkflow(updated);
      setStatus("failed");
      if (onWorkflowStateChange) onWorkflowStateChange(updated);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to process rejection.");
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* 1. Conversational Input & Execution Console */}
      <Card glass className="relative overflow-hidden border-primary/20 bg-gradient-to-b from-surface to-surface-lowest">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-primary/10 text-primary border border-primary/20 shadow-glow-blue">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-base font-bold text-foreground font-heading">
                  Cinematic AI Command Center
                </CardTitle>
                <CardDescription className="text-xs">
                  Autonomous multi-agent orchestration across 12 verified specialized agents
                </CardDescription>
              </div>
            </div>
            <span className="hidden sm:inline-flex px-2.5 py-1 text-[10px] font-mono font-bold rounded-full bg-secondary/15 text-secondary border border-secondary/25">
              NVIDIA Nemotron 3 Ultra Active
            </span>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Input Console Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleDispatchGoal(goal);
            }}
            className="relative flex items-center"
          >
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="Give a high-level objective (e.g. 'Analyze pending leads, draft follow-ups, schedule times, and ask for approval')..."
              className="w-full rounded-xl glass-panel bg-surface-lowest/90 pl-4 pr-28 py-3.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 shadow-inner font-sans"
            />
            <div className="absolute right-2 flex items-center gap-1.5">
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={status === "planning"}
                disabled={!goal.trim() || status === "planning"}
                leftIcon={<Send className="h-3.5 w-3.5" />}
                className="font-mono text-xs shadow-glow-blue"
              >
                Orchestrate
              </Button>
            </div>
          </form>

          {/* Suggested Multi-Agent Workflows */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
              <Lightbulb className="h-3.5 w-3.5 text-amber-400" />
              Suggested Multi-Agent Objectives:
            </span>
            <div className="flex flex-wrap gap-2">
              {suggestedPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleDispatchGoal(prompt)}
                  className="text-[11px] px-3 py-1.5 rounded-lg glass-panel bg-surface-container/60 hover:bg-surface-high border-border/60 text-muted-foreground hover:text-foreground transition-all text-left font-sans"
                >
                  "{prompt}"
                </button>
              ))}
            </div>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="p-3.5 rounded-xl border border-rose-500/30 bg-rose-950/20 text-rose-300 text-xs flex items-start gap-2.5 animate-fade-in">
              <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-bold block">Orchestrator Notice:</span>
                <p className="text-rose-300/90">{errorMessage}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 2. Live Interactive DAG Workflow Execution Graph */}
      {activeWorkflow && (
        <WorkflowDAGVisualizer
          workflow={activeWorkflow}
          onApprove={handleApprove}
          onReject={handleReject}
          isApproving={isApproving}
        />
      )}
    </div>
  );
};
