"use client";

import React, { useState } from "react";
import { ShieldCheck, AlertTriangle, Check, X, Edit3, ArrowRight, Database, Bot, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export interface DecisionGateApproval {
  id: string;
  workflowId: string;
  workflowTitle: string;
  agentName: string;
  stepKey: string;
  proposedAction: string;
  reasoning: string;
  impact: string;
  riskLevel: "LOW" | "MEDIUM" | "HIGH";
  confidence: number;
  dataSources: string[];
  createdAt: string;
}

export interface LiveDecisionGateProps {
  approvals?: DecisionGateApproval[];
  onApprove?: (approvalId: string, workflowId: string) => Promise<void>;
  onReject?: (approvalId: string, workflowId: string, reason?: string) => Promise<void>;
  className?: string;
}

export const DEFAULT_APPROVALS: DecisionGateApproval[] = [
  {
    id: "app-001",
    workflowId: "wf-outreach-882",
    workflowTitle: "Enterprise Fintech Pipeline Expansion",
    agentName: "OutreachAgent",
    stepKey: "step_dispatch_email",
    proposedAction: "Send personalized cold email sequence to 14 CTOs at Series-B fintech firms",
    reasoning:
      "LeadAgent scored prospect intent at 94%. ResearchAgent resolved recent hiring triggers. Personalized value proposition drafted.",
    impact:
      "14 external emails will be dispatched from verified mailbox. CRM contact status will transition to 'Outreach Sent'.",
    riskLevel: "MEDIUM",
    confidence: 94,
    dataSources: ["Lead CRM Database", "Research Agent Scraping", "Competitor Tech Stack Analysis"],
    createdAt: "Just now",
  },
];

export const LiveDecisionGate: React.FC<LiveDecisionGateProps> = ({
  approvals = DEFAULT_APPROVALS,
  onApprove,
  onReject,
  className = "",
}) => {
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [rejectModalId, setRejectModalId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [localApprovals, setLocalApprovals] = useState<DecisionGateApproval[]>(approvals);

  const handleApprove = async (app: DecisionGateApproval) => {
    setProcessingId(app.id);
    try {
      if (onApprove) {
        await onApprove(app.id, app.workflowId);
      }
      setLocalApprovals((prev) => prev.filter((a) => a.id !== app.id));
    } catch (e) {
      console.error("Approval execution error:", e);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (app: DecisionGateApproval) => {
    setProcessingId(app.id);
    try {
      if (onReject) {
        await onReject(app.id, app.workflowId, rejectReason);
      }
      setLocalApprovals((prev) => prev.filter((a) => a.id !== app.id));
      setRejectModalId(null);
      setRejectReason("");
    } catch (e) {
      console.error("Rejection execution error:", e);
    } finally {
      setProcessingId(null);
    }
  };

  if (localApprovals.length === 0) {
    return (
      <div className={`p-6 rounded-2xl glass-panel bg-card/60 border border-border/80 text-center space-y-2 ${className}`}>
        <div className="flex h-10 w-10 mx-auto items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <h4 className="text-sm font-bold text-foreground">All AI Decision Gates Clear</h4>
        <p className="text-xs text-muted-foreground">
          Autonomous agents have zero pending human approvals. Execution continuing unhindered.
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-amber-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider font-mono text-foreground">
            AI Decision Gates ({localApprovals.length} Pending)
          </h3>
        </div>
        <Badge variant="warning" size="sm">
          Human-in-the-Loop Active
        </Badge>
      </div>

      <div className="space-y-3.5">
        {localApprovals.map((app) => (
          <div
            key={app.id}
            className="p-5 rounded-2xl glass-panel bg-surface-lowest/90 border border-amber-500/30 shadow-xl space-y-4 transition-all"
          >
            {/* Header info */}
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-border/60">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/15 text-amber-400 border border-amber-500/30 font-bold">
                  <Bot className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-foreground flex items-center gap-2">
                    <span>{app.agentName}</span>
                    <span className="text-muted-foreground font-mono text-[10px]">({app.stepKey})</span>
                  </div>
                  <div className="text-[11px] text-muted-foreground">{app.workflowTitle}</div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Badge
                  variant={app.riskLevel === "HIGH" ? "danger" : app.riskLevel === "MEDIUM" ? "warning" : "success"}
                  size="sm"
                >
                  {app.riskLevel} RISK
                </Badge>
                <Badge variant="default" size="sm">
                  {app.confidence}% CONFIDENCE
                </Badge>
              </div>
            </div>

            {/* Proposed Action */}
            <div className="space-y-1">
              <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold">
                Proposed Action
              </span>
              <div className="text-xs font-semibold text-foreground bg-surface-container/60 p-2.5 rounded-xl border border-border/50">
                {app.proposedAction}
              </div>
            </div>

            {/* Why & Impact Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-surface/60 border border-border/50 space-y-1">
                <span className="text-[10px] font-mono uppercase text-primary font-bold">
                  Why (AI Reasoning)
                </span>
                <p className="text-[11px] text-muted-foreground leading-relaxed">{app.reasoning}</p>
              </div>

              <div className="p-3 rounded-xl bg-surface/60 border border-border/50 space-y-1">
                <span className="text-[10px] font-mono uppercase text-amber-400 font-bold">
                  External Impact
                </span>
                <p className="text-[11px] text-muted-foreground leading-relaxed">{app.impact}</p>
              </div>
            </div>

            {/* Data Sources Used */}
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-[10px] font-mono text-muted-foreground flex items-center gap-1 mr-1">
                <Database className="h-3 w-3" /> Data Context:
              </span>
              {app.dataSources.map((ds) => (
                <span
                  key={ds}
                  className="px-2 py-0.5 rounded-md bg-surface-high border border-border/60 text-[10px] font-mono text-foreground"
                >
                  {ds}
                </span>
              ))}
            </div>

            {/* Decision Action Buttons */}
            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-border/60">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setRejectModalId(app.id)}
                disabled={processingId === app.id}
                className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                leftIcon={<X className="h-3.5 w-3.5" />}
              >
                Reject Action
              </Button>

              <Button
                variant="primary"
                size="sm"
                onClick={() => handleApprove(app)}
                disabled={processingId === app.id}
                className="bg-emerald-600 hover:bg-emerald-500 text-white shadow-md glow-primary"
                leftIcon={<Check className="h-3.5 w-3.5" />}
              >
                {processingId === app.id ? "Authorizing..." : "Approve & Execute"}
              </Button>
            </div>

            {/* Rejection Reason Sub-panel */}
            {rejectModalId === app.id && (
              <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 space-y-2 animate-in fade-in">
                <label className="text-[11px] font-bold text-rose-300">
                  Provide reason for rejection (sent to LearningAgent for replanning):
                </label>
                <textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="e.g. Tone too aggressive, prospect not qualified yet..."
                  rows={2}
                  className="w-full p-2 rounded-lg bg-surface border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-rose-500"
                />
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setRejectModalId(null)}>
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleReject(app)}
                    className="bg-rose-600 hover:bg-rose-500 text-white"
                  >
                    Confirm Rejection
                  </Button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
