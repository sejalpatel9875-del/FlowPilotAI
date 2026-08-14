"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Toast, ToastType } from "@/components/ui/Toast";
import {
  Bot,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowLeft,
  Check,
  X,
  ShieldCheck,
  Activity,
  Terminal,
  Layers
} from "lucide-react";

export default function AgentRunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const runId = params.id as string;

  const [run, setRun] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessingApproval, setIsProcessingApproval] = useState(false);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchRunDetail();
  }, [runId]);

  const fetchRunDetail = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/agents/runs/${runId}`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setRun(data);
      } else {
        setToast({ type: "error", title: "Error", message: "Run log not found." });
      }
    } catch (err) {
      console.error("Failed to load run detail", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async () => {
    setIsProcessingApproval(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/agents/runs/${runId}/approve`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        setToast({ type: "success", title: "Action Approved", message: "Agent action has been approved and executed." });
        fetchRunDetail();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to approve action." });
    } finally {
      setIsProcessingApproval(false);
    }
  };

  const handleReject = async () => {
    setIsProcessingApproval(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/agents/runs/${runId}/reject`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        setToast({ type: "warning", title: "Action Rejected", message: "Agent action was rejected." });
        fetchRunDetail();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to reject action." });
    } finally {
      setIsProcessingApproval(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-8 text-center text-xs text-muted-foreground">
        Loading agent execution log...
      </div>
    );
  }

  if (!run) {
    return (
      <div className="p-8 text-center space-y-3">
        <h3 className="text-base font-semibold text-foreground">Run Log Not Found</h3>
        <Button variant="outline" size="sm" onClick={() => router.push("/agents")}>
          Return to Agents Hub
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link href="/agents" className="flex items-center text-xs text-muted-foreground hover:text-foreground gap-1 font-medium">
          <ArrowLeft className="h-4 w-4" /> Back to Agents Hub
        </Link>
        <Badge variant={run.status === "needs_approval" ? "failed" : "completed"} className="font-mono text-xs">
          Status: {run.status.toUpperCase()}
        </Badge>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Human Approval Banner if pending */}
      {run.status === "needs_approval" && (
        <Card glass className="border-amber-500/40 bg-amber-500/10 p-5 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-6 w-6 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-bold text-amber-200">Human Approval Required</h3>
                <p className="text-xs text-amber-300/80 mt-0.5">
                  Agent '{run.agentName}' requests permission to execute an external action. Review the details below before approving.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleReject}
                isLoading={isProcessingApproval}
                className="border-rose-500/40 text-rose-300 hover:bg-rose-500/20"
                leftIcon={<X className="h-4 w-4" />}
              >
                Reject Action
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleApprove}
                isLoading={isProcessingApproval}
                className="bg-emerald-600 hover:bg-emerald-500 text-white"
                leftIcon={<Check className="h-4 w-4" />}
              >
                Approve & Execute
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Main Execution Detail */}
      <Card glass className="space-y-6 p-6">
        <div className="flex items-center justify-between pb-4 border-b border-border/60">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold">
              <Bot className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-foreground">{run.agentName} Execution Log</h2>
              <span className="text-xs text-muted-foreground font-mono">Run ID: {run.runId} • {run.timestamp}</span>
            </div>
          </div>
        </div>

        {/* Input Query */}
        <div className="space-y-1.5 text-xs">
          <span className="font-semibold text-muted-foreground uppercase tracking-wider block text-[10px]">Input Query</span>
          <div className="p-3.5 rounded-xl glass-panel bg-secondary/30 text-foreground font-medium">
            {run.inputQuery}
          </div>
        </div>

        {/* Tools Used */}
        <div className="space-y-1.5 text-xs">
          <span className="font-semibold text-muted-foreground uppercase tracking-wider block text-[10px]">Tools Invoked</span>
          <div className="flex flex-wrap gap-1.5">
            {run.toolsUsed.map((t: string) => (
              <span key={t} className="px-2 py-1 rounded-lg bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 font-mono text-[10px]">
                🔧 {t}
              </span>
            ))}
          </div>
        </div>

        {/* Safe Execution Reasoning */}
        <div className="space-y-1.5 text-xs">
          <span className="font-semibold text-purple-300 uppercase tracking-wider block text-[10px] flex items-center gap-1">
            <ShieldCheck className="h-3.5 w-3.5" />
            Safe Execution Reasoning Summary
          </span>
          <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-200 italic font-mono">
            {run.reasoningSummary}
          </div>
          <span className="text-[10px] text-muted-foreground italic block">Note: Hidden raw chain-of-thought is stripped for security compliance.</span>
        </div>

        {/* Output Text */}
        <div className="space-y-1.5 text-xs">
          <span className="font-semibold text-muted-foreground uppercase tracking-wider block text-[10px]">Agent Output</span>
          <div className="p-4 rounded-xl glass-panel bg-secondary/40 border border-border/60 text-slate-200 font-mono whitespace-pre-wrap leading-relaxed">
            {run.outputText}
          </div>
        </div>
      </Card>
    </div>
  );
}
