"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Toast, ToastType } from "@/components/ui/Toast";
import {
  Bot,
  ArrowLeft,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  FileText
} from "lucide-react";

export default function AgentRunDetailPage() {
  const params = useParams();
  const runId = params.id as string;

  const [run, setRun] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isApproving, setIsApproving] = useState(false);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    if (runId) fetchRunDetail();
  }, [runId]);

  const fetchRunDetail = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/agents/runs/${runId}`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setRun(data);
      }
    } catch (err) {
      console.error("Failed to load run detail", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/agents/runs/${runId}/approve`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        setToast({ type: "success", title: "Action Approved", message: "Agent run status updated to completed." });
        fetchRunDetail();
      }
    } catch (err) {
      setToast({ type: "error", title: "Approval Failed", message: "Could not approve action." });
    } finally {
      setIsApproving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-8 text-center text-xs text-muted-foreground">
        Loading agent run details...
      </div>
    );
  }

  if (!run) {
    return (
      <div className="p-8 text-center space-y-4">
        <h3 className="text-lg font-bold text-foreground">Run Not Found</h3>
        <p className="text-xs text-muted-foreground">The requested agent execution run does not exist or is unauthorized.</p>
        <Link href="/agents">
          <Button variant="outline" size="sm" leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Agents
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/agents">
            <Button variant="outline" size="sm" leftIcon={<ArrowLeft className="h-4 w-4" />}>
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
              <Bot className="h-5 w-5 text-indigo-400" />
              Agent Run Detail: {run.agentName}
            </h1>
            <span className="text-xs font-mono text-muted-foreground">Run ID: {run.id}</span>
          </div>
        </div>

        <Badge variant={run.status === "needs_approval" ? "needs_approval" : run.status === "failed" ? "failed" : "completed"}>
          {run.status.toUpperCase()}
        </Badge>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
        <Card glass className="p-4 space-y-1">
          <span className="text-muted-foreground text-[10px]">Execution Latency</span>
          <p className="text-base font-bold text-foreground">{run.latencyMs} ms</p>
        </Card>

        <Card glass className="p-4 space-y-1">
          <span className="text-muted-foreground text-[10px]">Started At</span>
          <p className="text-base font-bold text-foreground">{run.startedAt || "N/A"}</p>
        </Card>

        <Card glass className="p-4 space-y-1">
          <span className="text-muted-foreground text-[10px]">Completed At</span>
          <p className="text-base font-bold text-foreground">{run.completedAt || "In Progress"}</p>
        </Card>
      </div>

      {/* Approval Alert if pending */}
      {run.status === "needs_approval" && (
        <Card glass className="p-4 bg-amber-500/10 border-amber-500/30 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-400" />
            <div>
              <h4 className="text-xs font-bold text-amber-300">Action Pending Approval</h4>
              <p className="text-[11px] text-amber-200/80">Outreach/Campaign draft requires human verification before dispatch.</p>
            </div>
          </div>
          <Button variant="primary" size="sm" onClick={handleApprove} isLoading={isApproving}>
            Approve & Execute
          </Button>
        </Card>
      )}

      {/* Execution Input & Output */}
      <div className="space-y-4">
        <Card glass className="p-5 space-y-2 font-mono">
          <span className="text-xs font-bold text-indigo-400">User Input Query</span>
          <p className="text-xs text-slate-200 whitespace-pre-wrap">{run.inputQuery}</p>
        </Card>

        <Card glass className="p-5 space-y-2 font-mono">
          <span className="text-xs font-bold text-emerald-400">Execution Output Summary</span>
          <p className="text-xs text-slate-200 whitespace-pre-wrap">{run.outputSummary || "No output."}</p>
        </Card>
      </div>
    </div>
  );
}
