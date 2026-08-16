"use client";

import React, { useState } from "react";
import { Workflow, WorkflowStep } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Play,
  ShieldAlert,
  Bot,
  ArrowRight,
  Maximize2,
  Minimize2,
  Layers,
  ChevronDown,
  ChevronUp,
  Cpu
} from "lucide-react";

interface WorkflowDAGVisualizerProps {
  workflow: Workflow;
  onApprove?: (approvalId: string) => void;
  onReject?: (approvalId: string) => void;
  isApproving?: boolean;
}

export const WorkflowDAGVisualizer: React.FC<WorkflowDAGVisualizerProps> = ({
  workflow,
  onApprove,
  onReject,
  isApproving,
}) => {
  const [selectedStep, setSelectedStep] = useState<WorkflowStep | null>(null);
  const [isExpanded, setIsExpanded] = useState(true);

  const steps = workflow.steps || [];

  const getStepStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return <Badge variant="completed" className="text-[10px] font-mono"><CheckCircle2 className="h-3 w-3 mr-1" /> COMPLETED</Badge>;
      case "RUNNING":
        return <Badge variant="running" className="text-[10px] font-mono"><Play className="h-3 w-3 mr-1 animate-pulse" /> RUNNING</Badge>;
      case "WAITING_FOR_APPROVAL":
        return <Badge variant="warning" className="text-[10px] font-mono animate-pulse"><ShieldAlert className="h-3 w-3 mr-1" /> WAITING APPROVAL</Badge>;
      case "FAILED":
        return <Badge variant="failed" className="text-[10px] font-mono"><AlertCircle className="h-3 w-3 mr-1" /> FAILED</Badge>;
      case "SKIPPED":
        return <Badge variant="secondary" className="text-[10px] font-mono">SKIPPED</Badge>;
      default:
        return <Badge variant="secondary" className="text-[10px] font-mono">PLANNED</Badge>;
    }
  };

  const getNodeBorderColor = (status: string) => {
    switch (status) {
      case "COMPLETED": return "border-emerald-500/50 bg-emerald-950/20";
      case "RUNNING": return "border-primary/70 bg-primary/15 shadow-glow-blue animate-glow-pulse";
      case "WAITING_FOR_APPROVAL": return "border-amber-500/80 bg-amber-950/30 shadow-glow-purple";
      case "FAILED": return "border-rose-500/70 bg-rose-950/25";
      default: return "border-border/70 bg-surface-container/60";
    }
  };

  return (
    <div className="rounded-2xl glass-panel border border-border/80 p-5 space-y-4 overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border/60">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20 shadow-glow-blue">
            <Layers className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-foreground font-heading">Multi-Agent Execution Graph</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-secondary/20 text-secondary border border-secondary/30">
                {workflow.status}
              </span>
            </div>
            <p className="text-xs text-muted-foreground line-clamp-1 max-w-xl">
              Goal: {workflow.goal}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-muted-foreground">
          <span>{workflow.completedSteps}/{workflow.totalSteps} Steps</span>
          <span>•</span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg hover:bg-surface-high text-muted-foreground hover:text-foreground transition-colors"
          >
            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-6">
          {/* Visual DAG Nodes Flow */}
          <div className="relative overflow-x-auto py-4">
            <div className="flex items-center gap-3 min-w-max pb-2">
              {/* Planner Root Node */}
              <div className="flex flex-col items-center">
                <div className="p-3.5 rounded-xl border border-secondary/50 bg-secondary/15 text-center min-w-[140px] shadow-sm">
                  <div className="flex items-center justify-center gap-1.5 text-secondary text-xs font-bold mb-1">
                    <Cpu className="h-4 w-4" />
                    <span>Planner</span>
                  </div>
                  <span className="text-[10px] font-mono text-muted-foreground">Task Decomposition</span>
                  <div className="mt-2">
                    <Badge variant="completed" className="text-[9px] font-mono">PLANNED</Badge>
                  </div>
                </div>
              </div>

              {/* Steps Nodes */}
              {steps.map((step, idx) => (
                <React.Fragment key={step.id}>
                  {/* Directed Edge Arrow */}
                  <div className="flex items-center justify-center text-primary/60 px-1">
                    <ArrowRight className="h-4 w-4 animate-pulse" />
                  </div>

                  {/* Step Node Card */}
                  <div
                    onClick={() => setSelectedStep(step)}
                    className={`cursor-pointer p-4 rounded-xl border transition-all duration-200 min-w-[200px] max-w-[240px] hover:scale-[1.02] ${getNodeBorderColor(
                      step.status
                    )}`}
                  >
                    <div className="flex items-start justify-between gap-1 mb-2">
                      <div className="flex items-center gap-1.5">
                        <Bot className="h-4 w-4 text-primary" />
                        <span className="text-xs font-bold text-foreground font-heading truncate">
                          {step.agent}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-muted-foreground">
                        #{idx + 1}
                      </span>
                    </div>

                    <p className="text-[11px] text-muted-foreground line-clamp-2 mb-3 min-h-[32px]">
                      {step.description || step.action}
                    </p>

                    <div className="flex items-center justify-between pt-2 border-t border-border/40">
                      {getStepStatusBadge(step.status)}
                      <span className="text-[10px] font-mono text-muted-foreground">
                        {step.latencyMs ? `${step.latencyMs}ms` : "—"}
                      </span>
                    </div>
                  </div>
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Pending Approval Banner if WAITING_FOR_APPROVAL */}
          {workflow.status === "WAITING_FOR_APPROVAL" && workflow.pendingApprovals && workflow.pendingApprovals.length > 0 && (
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fade-in">
              <div className="flex items-start gap-3">
                <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider">
                    Human Approval Required
                  </h4>
                  <p className="text-xs text-amber-200/90 mt-0.5">
                    {workflow.pendingApprovals[0].proposedAction}
                  </p>
                </div>
              </div>

              {onApprove && onReject && (
                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => onApprove(workflow.pendingApprovals![0].id)}
                    isLoading={isApproving}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs"
                  >
                    Approve Action
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onReject(workflow.pendingApprovals![0].id)}
                    disabled={isApproving}
                    className="border-rose-500/40 text-rose-300 hover:bg-rose-950/30 font-mono text-xs"
                  >
                    Reject
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Selected Step Inspection Details Panel */}
          {selectedStep && (
            <div className="p-4 rounded-xl glass-panel bg-surface-lowest/90 border border-border/80 space-y-3 animate-fade-in text-xs">
              <div className="flex items-center justify-between border-b border-border/60 pb-2">
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4 text-primary" />
                  <span className="font-bold text-foreground">{selectedStep.agent} — {selectedStep.stepKey}</span>
                </div>
                <button
                  onClick={() => setSelectedStep(null)}
                  className="text-muted-foreground hover:text-foreground text-xs font-mono"
                >
                  Close ✕
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-[11px]">
                <div>
                  <span className="text-muted-foreground block">Action:</span>
                  <span className="text-foreground font-semibold">{selectedStep.action}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Status:</span>
                  <span className="text-primary font-semibold">{selectedStep.status}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Latency:</span>
                  <span className="text-tertiary font-semibold">{selectedStep.latencyMs}ms</span>
                </div>
              </div>

              {selectedStep.output && (
                <div className="space-y-1 pt-2 border-t border-border/40 font-mono">
                  <span className="text-muted-foreground block text-[10px] uppercase font-bold">Step Normalized Output:</span>
                  <div className="p-3 rounded-lg bg-surface-high/60 border border-border/50 text-foreground whitespace-pre-wrap max-h-48 overflow-y-auto">
                    {selectedStep.output.output || selectedStep.output.summary || JSON.stringify(selectedStep.output, null, 2)}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
