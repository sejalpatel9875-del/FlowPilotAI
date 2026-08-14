"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Tabs } from "@/components/ui/Tabs";
import {
  Zap,
  Play,
  Pause,
  Plus,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  ShieldAlert,
  Layers,
  Cpu,
  RefreshCw,
  Terminal,
  FileText,
  HelpCircle,
  Activity,
  Sliders,
  Check
} from "lucide-react";

interface AutomationItem {
  id: string;
  name: string;
  description?: string;
  triggerType: string;
  actionType: string;
  requiresApproval: boolean;
  status: "ACTIVE" | "PAUSED";
  isActive: boolean;
  aiDecisionPrompt?: string;
  runsCount: number;
  lastRun?: string;
}

interface AutomationRun {
  id: string;
  automationId: string;
  triggerEvent: string;
  status: "SUCCESS" | "PENDING_APPROVAL" | "FAILED";
  aiDecisionSummary?: string;
  logs?: string;
  errorMessage?: string;
  executedAt: string;
}

export default function AutomationsPage() {
  const [automations, setAutomations] = useState<AutomationItem[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [runs, setRuns] = useState<AutomationRun[]>([]);
  const [activeTab, setActiveTab] = useState("automations");

  // Create Automation Modal
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [autoName, setAutoName] = useState("");
  const [triggerType, setTriggerType] = useState("NEW_LEAD");
  const [actionType, setActionType] = useState("GENERATE_DRAFT");
  const [aiDecisionPrompt, setAiDecisionPrompt] = useState("");
  const [requiresApproval, setRequiresApproval] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Test Run State
  const [testingId, setTestingId] = useState<string | null>(null);

  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchAutomationsData();
    fetchRunLogs();
  }, []);

  const fetchAutomationsData = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/automations", {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setAutomations(data.automations || []);
        setTemplates(data.templates || []);
      }
    } catch (err) {
      console.error("Failed to load automations data", err);
    }
  };

  const fetchRunLogs = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/automations/runs", {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setRuns(data.runs || []);
      }
    } catch (err) {
      console.error("Failed to load run logs", err);
    }
  };

  const handleCreateAutomation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!autoName) return;

    setIsSubmitting(true);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/automations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: autoName,
          triggerType,
          actionType,
          aiDecisionPrompt: aiDecisionPrompt || `Evaluate trigger event '${triggerType}' and execute '${actionType}'.`,
          requiresApproval,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to create automation.");
      }

      setToast({ type: "success", title: "Automation Workflow Created", message: `7-stage workflow initialized with ${requiresApproval ? "Approval Gatekeeper" : "Auto-Execution"}.` });
      setIsCreateModalOpen(false);
      setAutoName("");
      setAiDecisionPrompt("");
      fetchAutomationsData();
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInstallTemplate = async (template: any) => {
    setToast(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/automations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: template.name,
          triggerType: template.triggerType,
          actionType: template.actionType,
          aiDecisionPrompt: template.aiDecisionPrompt,
          requiresApproval: template.requiresApproval,
          description: template.description,
        }),
      });

      if (res.ok) {
        setToast({ type: "success", title: "Template Installed", message: `Activated '${template.name}'.` });
        fetchAutomationsData();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to install template." });
    }
  };

  const handleToggleStatus = async (automationId: string, currentStatus: string) => {
    const nextStatus = currentStatus === "ACTIVE" ? "PAUSED" : "ACTIVE";
    try {
      const res = await fetch(`http://localhost:8000/api/v1/automations/${automationId}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ status: nextStatus }),
      });

      if (res.ok) {
        setToast({ type: "info", title: "Status Updated", message: `Automation set to ${nextStatus}.` });
        fetchAutomationsData();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to update status." });
    }
  };

  const handleTestExecution = async (automationId: string) => {
    setTestingId(automationId);
    setToast(null);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/automations/${automationId}/test`, {
        method: "POST",
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Test run failed.");
      }

      const data = await res.json();
      setToast({ type: "success", title: "Test Execution Completed", message: `Status: ${data.status}. 7-Stage pipeline executed.` });
      fetchAutomationsData();
      fetchRunLogs();
    } catch (err: any) {
      setToast({ type: "error", title: "Test Failed", message: err.message });
    } finally {
      setTestingId(null);
    }
  };

  const getRunBadgeVariant = (status: string) => {
    switch (status) {
      case "SUCCESS": return "completed";
      case "PENDING_APPROVAL": return "purple";
      case "FAILED": return "danger";
      default: return "secondary";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Zap className="h-6 w-6 text-amber-400" />
            FlowPilot Automation Engine
          </h1>
          <p className="text-xs text-muted-foreground">
            7-Stage Workflow Architecture: TRIGGER → CONDITION → AI DECISION → ACTION → APPROVAL → EXECUTION → AUDIT.
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={() => setIsCreateModalOpen(true)}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          New Automation Workflow
        </Button>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* 7-STAGE ARCHITECTURE VISUAL BANNER */}
      <Card glass className="p-4 bg-gradient-to-r from-amber-950/20 via-card to-purple-950/20 border-amber-500/30">
        <h4 className="text-xs font-bold text-foreground mb-3 font-mono flex items-center gap-2">
          <Cpu className="h-4 w-4 text-amber-400" /> 7-Stage Automation Execution Pipeline
        </h4>
        <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono">
          <div className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-300 border border-amber-500/30 font-bold">1. TRIGGER</div>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
          <div className="px-2.5 py-1 rounded-lg bg-secondary/50 text-slate-300 border border-border/60">2. CONDITION</div>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
          <div className="px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-300 border border-purple-500/30 font-bold">3. AI DECISION</div>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
          <div className="px-2.5 py-1 rounded-lg bg-sky-500/10 text-sky-300 border border-sky-500/30 font-bold">4. ACTION</div>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
          <div className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-bold">5. APPROVAL</div>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
          <div className="px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">6. EXECUTION</div>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
          <div className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700">7. AUDIT</div>
        </div>
      </Card>

      {/* Tabs Switcher */}
      <Tabs
        tabs={[
          { id: "automations", label: `Active Workflows (${automations.length})` },
          { id: "templates", label: `Pre-Built Templates (${templates.length})` },
          { id: "runs", label: `Execution & Failure Logs (${runs.length})` },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {/* TAB 1: ACTIVE AUTOMATIONS */}
      {activeTab === "automations" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {automations.map((auto) => (
              <Card key={auto.id} glass className="p-5 space-y-4 hover:border-amber-500/40 transition-all">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/50 pb-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-foreground">{auto.name}</h3>
                      <Badge variant={auto.status === "ACTIVE" ? "completed" : "secondary"}>
                        {auto.status}
                      </Badge>
                    </div>
                    {auto.description && (
                      <p className="text-xs text-muted-foreground">{auto.description}</p>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleToggleStatus(auto.id, auto.status)}
                      className={`p-2 rounded-xl text-xs font-mono font-bold flex items-center gap-1.5 border transition-all ${
                        auto.status === "ACTIVE"
                          ? "bg-amber-500/10 text-amber-300 border-amber-500/30 hover:bg-amber-500/20"
                          : "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20"
                      }`}
                    >
                      {auto.status === "ACTIVE" ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                      {auto.status === "ACTIVE" ? "Pause Workflow" : "Resume Workflow"}
                    </button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTestExecution(auto.id)}
                      isLoading={testingId === auto.id}
                      leftIcon={<Play className="h-3.5 w-3.5 text-purple-400" />}
                    >
                      Test Run
                    </Button>
                  </div>
                </div>

                {/* Workflow Configuration Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
                  <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
                    <span className="text-muted-foreground block text-[10px]">Trigger Event:</span>
                    <span className="font-bold text-amber-300">{auto.triggerType}</span>
                  </div>

                  <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
                    <span className="text-muted-foreground block text-[10px]">AI Decision Rule:</span>
                    <span className="font-bold text-purple-300 truncate block">{auto.aiDecisionPrompt || "Evaluate trigger condition & context."}</span>
                  </div>

                  <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
                    <span className="text-muted-foreground block text-[10px]">Action & Gatekeeper:</span>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sky-300">{auto.actionType}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {auto.requiresApproval ? "Approval Gatekeeper" : "Auto-Execute"}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: PRE-BUILT TEMPLATES */}
      {activeTab === "templates" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {templates.map((tpl, idx) => (
            <Card key={idx} glass className="p-5 space-y-4 border-purple-500/30 hover:border-purple-500/60 transition-all flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-foreground">{tpl.name}</h3>
                  <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20 text-[10px] font-mono font-bold">
                    PRE-BUILT TEMPLATE
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">{tpl.description}</p>

                <div className="pt-2 flex items-center gap-2 font-mono text-[11px]">
                  <span className="px-2 py-1 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 font-bold">
                    TRIGGER: {tpl.triggerType}
                  </span>
                  <ArrowRight className="h-3 w-3 text-muted-foreground" />
                  <span className="px-2 py-1 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20 font-bold">
                    ACTION: {tpl.actionType}
                  </span>
                </div>
              </div>

              <div className="pt-3 border-t border-border/40 flex items-center justify-end">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleInstallTemplate(tpl)}
                  leftIcon={<Check className="h-3.5 w-3.5" />}
                >
                  Activate Template
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* TAB 3: EXECUTION & FAILURE LOGS */}
      {activeTab === "runs" && (
        <Card glass className="overflow-hidden border-border/60">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-secondary/40 border-b border-border/60 text-muted-foreground uppercase text-[10px]">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Trigger Event</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">AI Decision Summary</th>
                  <th className="px-4 py-3">Audit Logs</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {runs.map((run) => (
                  <tr key={run.id} className="hover:bg-secondary/20 transition-colors">
                    <td className="px-4 py-3 text-muted-foreground">{run.executedAt}</td>
                    <td className="px-4 py-3 font-bold text-amber-300">{run.triggerEvent}</td>
                    <td className="px-4 py-3">
                      <Badge variant={getRunBadgeVariant(run.status)}>
                        {run.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-slate-300 max-w-xs truncate">{run.aiDecisionSummary || "Execution validated by AI agent."}</td>
                    <td className="px-4 py-3 text-muted-foreground max-w-xs truncate">{run.logs}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* NEW AUTOMATION WORKFLOW MODAL */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Automation Workflow"
      >
        <form onSubmit={handleCreateAutomation} className="space-y-4 text-xs">
          <div className="space-y-1">
            <label className="font-semibold text-foreground">Automation Name *</label>
            <input
              type="text"
              required
              placeholder="e.g. Auto-Draft Pitch on Qualified Lead"
              value={autoName}
              onChange={(e) => setAutoName(e.target.value)}
              className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="font-semibold text-foreground">Trigger Event (10 Triggers)</label>
              <select
                value={triggerType}
                onChange={(e) => setTriggerType(e.target.value)}
                className="w-full rounded-xl glass-panel bg-secondary/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 font-mono"
              >
                <option value="NEW_LEAD">New Lead</option>
                <option value="LEAD_QUALIFIED">Lead Qualified</option>
                <option value="OUTREACH_SENT">Outreach Sent</option>
                <option value="NO_RESPONSE">No Response</option>
                <option value="REPLY_RECEIVED">Reply Received</option>
                <option value="TASK_DUE">Task Due</option>
                <option value="DEADLINE_APPROACHING">Deadline Approaching</option>
                <option value="LEARNING_BEHIND_SCHEDULE">Learning Behind Schedule</option>
                <option value="DAILY_SCHEDULE">Daily Schedule</option>
                <option value="WEEKLY_REVIEW">Weekly Review</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-foreground">Target Action (7 Actions)</label>
              <select
                value={actionType}
                onChange={(e) => setActionType(e.target.value)}
                className="w-full rounded-xl glass-panel bg-secondary/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 font-mono"
              >
                <option value="GENERATE_DRAFT">Generate draft</option>
                <option value="CREATE_TASK">Create task</option>
                <option value="CREATE_FOLLOW_UP">Create follow-up</option>
                <option value="UPDATE_LEAD">Update lead</option>
                <option value="GENERATE_REPORT">Generate report</option>
                <option value="CREATE_LEARNING_SESSION">Create learning session</option>
                <option value="SEND_NOTIFICATION">Send notification</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-foreground">AI Decision Prompt Rule</label>
            <textarea
              rows={3}
              placeholder="Instructions for AI decision evaluation step..."
              value={aiDecisionPrompt}
              onChange={(e) => setAiDecisionPrompt(e.target.value)}
              className="w-full rounded-xl glass-panel bg-secondary/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 font-mono"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="requiresApproval"
              checked={requiresApproval}
              onChange={(e) => setRequiresApproval(e.target.checked)}
              className="rounded border-border/80 text-primary focus:ring-primary"
            />
            <label htmlFor="requiresApproval" className="text-xs font-mono text-foreground cursor-pointer">
              Enable Human Approval Gatekeeper (Requires review before final execution)
            </label>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" type="button" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSubmitting}>
              Create Workflow
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
