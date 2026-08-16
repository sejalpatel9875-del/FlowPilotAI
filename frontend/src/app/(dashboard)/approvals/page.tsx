"use client";

import React, { useState, useEffect } from "react";
import { Workflow, WorkflowApproval } from "@/types";
import { apiService } from "@/services/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Toast, ToastType } from "@/components/ui/Toast";
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  Bot,
  AlertTriangle,
  RotateCcw,
  ShieldCheck,
  Send
} from "lucide-react";

export default function HumanApprovalCenterPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
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
      await apiService.approveWorkflowAction(workflowId, approvalId, "Approved via Human Approval Center");
      setToast({ type: "success", title: "Action Approved", message: "Approved side effect dispatched and workflow resumed." });
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
    try {
      await apiService.rejectWorkflowAction(workflowId, approvalId, "Rejected via Human Approval Center");
      setToast({ type: "warning", title: "Action Rejected", message: "Side effect blocked. Workflow concluded safely." });
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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2 font-heading">
            <ShieldCheck className="h-6 w-6 text-amber-400" />
            Human-in-the-Loop Approval Center
          </h1>
          <p className="text-xs text-muted-foreground">
            Mandatory authorization gate for external actions, communications, and irreversible side effects.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="warning" className="font-mono text-xs">
            {totalPending} Actions Pending Review
          </Badge>
          <Button variant="outline" size="sm" onClick={loadApprovals} leftIcon={<RotateCcw className="h-3.5 w-3.5" />}>
            Refresh
          </Button>
        </div>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Approvals Queue */}
      {isLoading ? (
        <Card glass className="p-8 text-center text-xs text-muted-foreground">
          Scanning workflow state machines for pending authorization gates...
        </Card>
      ) : workflows.length === 0 ? (
        <Card glass className="p-12 text-center space-y-3">
          <div className="p-3.5 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 w-fit mx-auto">
            <CheckCircle2 className="h-8 w-8" />
          </div>
          <h3 className="text-base font-bold text-foreground font-heading">Approval Queue Clean</h3>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            No workflows currently require human authorization. All safe autonomous steps have executed according to policy.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {workflows.map((wf) =>
            (wf.pendingApprovals || []).map((approval) => (
              <Card key={approval.id} glass className="p-6 space-y-4 border-l-4 border-l-amber-500">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-1.5 max-w-2xl">
                    <div className="flex items-center gap-2">
                      <Badge variant="warning" className="text-[10px] font-mono">
                        APPROVAL REQUIRED
                      </Badge>
                      <span className="text-xs font-mono text-muted-foreground">Workflow ID: {wf.id.slice(0, 8)}...</span>
                    </div>

                    <h3 className="text-base font-bold text-foreground font-heading">
                      {wf.title || wf.goal}
                    </h3>
                    <p className="text-xs text-slate-300 font-mono bg-surface-lowest/80 p-3 rounded-xl border border-border/60">
                      {approval.proposedAction}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleApprove(wf.id, approval.id)}
                      isLoading={processingId === approval.id}
                      leftIcon={<CheckCircle2 className="h-4 w-4" />}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs"
                    >
                      Authorize Action
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleReject(wf.id, approval.id)}
                      disabled={processingId === approval.id}
                      leftIcon={<XCircle className="h-4 w-4" />}
                      className="border-rose-500/40 text-rose-300 hover:bg-rose-950/30 font-mono text-xs"
                    >
                      Reject
                    </Button>
                  </div>
                </div>

                {/* Workflow Prerequisite Steps Summary */}
                {wf.steps && (
                  <div className="pt-3 border-t border-border/40 space-y-2">
                    <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">
                      Prerequisite Completed Steps in DAG:
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {wf.steps
                        .filter((s) => s.status === "COMPLETED")
                        .map((s) => (
                          <div key={s.id} className="px-2.5 py-1 rounded-lg bg-surface-container/60 border border-border/40 text-[10px] font-mono text-slate-300 flex items-center gap-1.5">
                            <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                            <span>{s.agent}: {s.action}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}
