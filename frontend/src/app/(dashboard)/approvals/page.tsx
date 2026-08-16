"use client";

import React, { useState, useEffect } from "react";
import { SystemStatusBar } from "@/components/mission-control/SystemStatusBar";
import { Workflow, WorkflowApproval } from "@/types";
import { apiService } from "@/services/api";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Toast, ToastType } from "@/components/ui/Toast";
import {
  ShieldCheck,
  Check,
  X,
  Bot,
  AlertTriangle,
  RotateCcw,
  Database,
  Sparkles,
  ArrowRight,
  Shield,
  Activity,
  CheckCircle2,
} from "lucide-react";

export default function HumanApprovalCenterPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState<Record<string, string>>({});
  const [activeRejectModal, setActiveRejectModal] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    setIsLoading(true);
    try {
      const data = await apiService.listWorkflows("WAITING_FOR_APPROVAL");
      const wfsWithDetails = await Promise.all(
        (data.workflows || []).map(async (w) => {
          try {
            return await apiService.getWorkflow(w.id);
          } catch {
            return w;
          }
        })
      );
      setWorkflows(wfsWithDetails.filter((w) => w.pendingApprovals && w.pendingApprovals.length > 0));
    } catch (err: any) {
      console.error("Failed to load approvals", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (workflowId: string, approvalId: string) => {
    setProcessingId(approvalId);
    setToast(null);
    try {
      await apiService.approveWorkflowAction(workflowId, approvalId, "Authorized by Human Operator");
      setToast({
        type: "success",
        title: "Action Approved & Executed",
        message: "Side-effect dispatched via distributed worker queue.",
      });
      await loadApprovals();
    } catch (err: any) {
      setToast({ type: "error", title: "Approval Failed", message: err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (workflowId: string, approvalId: string) => {
    setProcessingId(approvalId);
    setToast(null);
    const reason = rejectReason[approvalId] || "Rejected by Human Operator";
    try {
      await apiService.rejectWorkflowAction(workflowId, approvalId, reason);
      setToast({
        type: "warning",
        title: "Action Blocked",
        message: "Side effect terminated safely. Workflow recorded as rejected.",
      });
      setActiveRejectModal(null);
      await loadApprovals();
    } catch (err: any) {
      setToast({ type: "error", title: "Rejection Failed", message: err.message });
    } finally {
      setProcessingId(null);
    }
  };

  const totalPending = workflows.reduce((acc, w) => acc + (w.pendingApprovals?.length || 0), 0);

  return (
    <div className="space-y-6">
      {/* 1. Top System Status Strip */}
      <SystemStatusBar
        activeAgentsCount={12}
        runningWorkflowsCount={3}
        pendingApprovalsCount={totalPending}
        systemHealth={99.4}
      />

      {/* 2. Header Banner */}
      <div className="p-5 rounded-2xl glass-panel bg-card/80 border border-border/80 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 font-mono text-xs text-amber-400 font-bold">
            <ShieldCheck className="h-4 w-4" />
            <span>AI DECISION GATE ARCHITECTURE</span>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-foreground mt-0.5">
            Human-in-the-Loop Authorization Center
          </h1>
          <p className="text-xs text-muted-foreground">
            Authoritative human boundary for irreversible side-effects, external communications, and policy triggers.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant={totalPending > 0 ? "warning" : "success"} size="md">
            {totalPending} ACTIONS REQUIRING AUTHORIZATION
          </Badge>
          <Button
            variant="glass"
            size="sm"
            onClick={loadApprovals}
            disabled={isLoading}
            leftIcon={<RotateCcw className="h-3.5 w-3.5" />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* 3. Empty State or Approval Decision Gate List */}
      {workflows.length === 0 ? (
        <div className="p-12 rounded-2xl glass-panel bg-card/60 border border-border/80 text-center space-y-3">
          <div className="flex h-12 w-12 mx-auto items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-md">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <h3 className="text-base font-bold text-foreground">All Decision Gates Clear</h3>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            Zero pending human authorizations in queue. All autonomous agents are operating within designated policy boundaries.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {workflows.map((wf) =>
            (wf.pendingApprovals || []).map((approval) => (
              <div
                key={approval.id}
                className="p-6 rounded-2xl glass-panel bg-surface-lowest/90 border border-amber-500/30 shadow-xl space-y-4 transition-all"
              >
                {/* Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border/60">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/15 text-amber-400 border border-amber-500/30 font-bold">
                      <Bot className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-foreground">
                          Workflow: {wf.title || wf.goal}
                        </span>
                        <span className="text-muted-foreground font-mono text-xs">
                          ({approval.stepKey || "Side Effect"})
                        </span>
                      </div>
                      <span className="text-xs text-muted-foreground font-mono">
                        Workflow ID: {wf.id}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 font-mono text-xs">
                    <Badge variant="warning" size="sm">
                      MEDIUM RISK
                    </Badge>
                    <Badge variant="default" size="sm">
                      94% CONFIDENCE
                    </Badge>
                  </div>
                </div>

                {/* Proposed Action Box */}
                <div className="space-y-1">
                  <span className="text-[10px] font-mono uppercase text-muted-foreground font-bold">
                    AI Wants to Perform
                  </span>
                  <div className="p-3 rounded-xl bg-surface-container/70 border border-border/60 text-xs font-semibold text-foreground">
                    {approval.proposedAction || "Execute external side effect action"}
                  </div>
                </div>

                {/* Reasoning & Impact Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-3.5 rounded-xl bg-surface/70 border border-border/50 space-y-1.5">
                    <span className="text-[10px] font-mono uppercase text-primary font-bold">
                      Why (AI Reasoning Summary)
                    </span>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      Lead intent qualified above 90% threshold. Contextual research and personalized messaging synthesized.
                      Requires final human oversight before external dispatch.
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-surface/70 border border-border/50 space-y-1.5">
                    <span className="text-[10px] font-mono uppercase text-amber-400 font-bold">
                      External Impact
                    </span>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      External communication will be transmitted and state transitions recorded in immutable audit log.
                    </p>
                  </div>
                </div>

                {/* Data Used */}
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[10px] font-mono text-muted-foreground flex items-center gap-1 mr-1">
                    <Database className="h-3 w-3" /> Data Context:
                  </span>
                  {["Tenant Lead Database", "Research Agent Scraping", "CRM Activity History"].map((ds) => (
                    <span
                      key={ds}
                      className="px-2 py-0.5 rounded-md bg-surface-high border border-border/60 text-[10px] font-mono text-foreground"
                    >
                      {ds}
                    </span>
                  ))}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-end gap-3 pt-3 border-t border-border/60">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setActiveRejectModal(approval.id)}
                    disabled={processingId === approval.id}
                    className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                    leftIcon={<X className="h-4 w-4" />}
                  >
                    Reject Action
                  </Button>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleApprove(wf.id, approval.id)}
                    disabled={processingId === approval.id}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white shadow-md glow-primary font-semibold"
                    leftIcon={<Check className="h-4 w-4" />}
                  >
                    {processingId === approval.id ? "Authorizing..." : "Approve & Execute"}
                  </Button>
                </div>

                {/* Rejection Reason Sub-panel */}
                {activeRejectModal === approval.id && (
                  <div className="mt-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 space-y-2.5 animate-in fade-in">
                    <label className="text-xs font-bold text-rose-300">
                      Reason for rejection (communicated to agent for replanning):
                    </label>
                    <textarea
                      value={rejectReason[approval.id] || ""}
                      onChange={(e) =>
                        setRejectReason((prev) => ({ ...prev, [approval.id]: e.target.value }))
                      }
                      placeholder="e.g. Tone too aggressive, prospect not qualified yet..."
                      rows={2}
                      className="w-full p-2.5 rounded-lg bg-surface border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-rose-500 font-mono"
                    />
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={() => setActiveRejectModal(null)}>
                        Cancel
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleReject(wf.id, approval.id)}
                        className="bg-rose-600 hover:bg-rose-500 text-white"
                      >
                        Confirm Rejection
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Toast Notification */}
      {toast && <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />}
    </div>
  );
}
