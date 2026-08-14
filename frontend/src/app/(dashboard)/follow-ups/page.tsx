"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Tabs } from "@/components/ui/Tabs";
import {
  Clock,
  Sparkles,
  Send,
  StopCircle,
  HelpCircle,
  CheckCircle2,
  Calendar,
  AlertCircle,
  FileText,
  Building,
  User,
  Plus,
  Play,
  ArrowRight,
  ShieldCheck,
  RefreshCw
} from "lucide-react";

interface FollowUpItem {
  id: string;
  sequenceId: string;
  leadId: string;
  company: string;
  leadName: string;
  leadEmail: string;
  leadStatus: string;
  stepNumber: number;
  delayDays: number;
  dueDate: string;
  status: "DUE" | "UPCOMING" | "WAITING" | "COMPLETED" | "STOPPED";
  draftBody?: string;
  aiReasoning?: string;
  sentAt?: string;
}

interface LeadItem {
  id: string;
  company: string;
  name: string;
}

export default function FollowUpsPage() {
  const [activeQueue, setActiveQueue] = useState("due_today");
  const [items, setItems] = useState<FollowUpItem[]>([]);
  const [leads, setLeads] = useState<LeadItem[]>([]);

  // Start Sequence Modal
  const [isStartModalOpen, setIsStartModalOpen] = useState(false);
  const [selectedLeadId, setSelectedLeadId] = useState("");
  const [isStarting, setIsStarting] = useState(false);

  // AI Action States
  const [loadingAiId, setLoadingAiId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchFollowUps(activeQueue);
    fetchLeads();
  }, [activeQueue]);

  const fetchFollowUps = async (queueName: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/follow-ups?queue=${queueName}`, {
        credentials: "include",
      });
      if (res.ok) {
        setItems((await res.json()).items || []);
      }
    } catch (err) {
      console.error("Failed to load follow-up queue", err);
    }
  };

  const fetchLeads = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/leads", {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setLeads(data.leads || []);
        if (data.leads && data.leads.length > 0) {
          setSelectedLeadId(data.leads[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to load leads", err);
    }
  };

  const handleStartSequence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLeadId) return;

    setIsStarting(true);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/follow-ups/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ leadId: selectedLeadId }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to start follow-up sequence.");
      }

      const data = await res.json();
      setToast({ type: "success", title: "Sequence Initialized", message: data.message });
      setIsStartModalOpen(false);
      fetchFollowUps(activeQueue);
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    } finally {
      setIsStarting(false);
    }
  };

  const handleExplainWhy = async (id: string) => {
    setLoadingAiId(id);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/follow-ups/${id}/explain`, {
        method: "POST",
        credentials: "include",
      });

      if (res.ok) {
        const data = await res.json();
        setItems((prev) =>
          prev.map((item) => (item.id === id ? { ...item, aiReasoning: data.aiReasoning } : item))
        );
        setToast({ type: "success", title: "AI Analysis Complete", message: "Retrieved follow-up rationale." });
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to generate AI explanation." });
    } finally {
      setLoadingAiId(null);
    }
  };

  const handleGenerateDraft = async (id: string) => {
    setLoadingAiId(id);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/follow-ups/${id}/generate-draft`, {
        method: "POST",
        credentials: "include",
      });

      if (res.ok) {
        const data = await res.json();
        setItems((prev) =>
          prev.map((item) => (item.id === id ? { ...item, draftBody: data.draftBody } : item))
        );
        setToast({ type: "success", title: "Draft Generated", message: "Follow-up email copy ready." });
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to generate draft." });
    } finally {
      setLoadingAiId(null);
    }
  };

  const handleSendFollowUp = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/follow-ups/${id}/send`, {
        method: "POST",
        credentials: "include",
      });

      if (res.ok) {
        setToast({ type: "success", title: "Follow-Up Sent", message: "Sequence step completed." });
        fetchFollowUps(activeQueue);
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to send follow-up." });
    }
  };

  const handleStopSequence = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/follow-ups/${id}/stop`, {
        method: "POST",
        credentials: "include",
      });

      if (res.ok) {
        setToast({ type: "warning", title: "Sequence Stopped", message: "Follow-up sequence halted." });
        fetchFollowUps(activeQueue);
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to stop sequence." });
    }
  };

  const getQueueBadge = (st: string) => {
    switch (st) {
      case "DUE": return <span className="px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono font-bold text-[10px]">DUE TODAY</span>;
      case "UPCOMING": return <span className="px-2.5 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30 font-mono font-bold text-[10px]">UPCOMING</span>;
      case "WAITING": return <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono font-bold text-[10px]">WAITING REPLY</span>;
      case "COMPLETED": return <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono font-bold text-[10px]">COMPLETED</span>;
      case "STOPPED": return <span className="px-2.5 py-0.5 rounded-full bg-slate-500/20 text-slate-300 border border-slate-500/30 font-mono font-bold text-[10px]">STOPPED</span>;
      default: return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Clock className="h-6 w-6 text-amber-400" />
            Intelligent Follow-Up Engine
          </h1>
          <p className="text-xs text-muted-foreground">
            3-step automated cadence (3d → 7d → 14d) with automatic stop triggers upon client reply.
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={() => setIsStartModalOpen(true)}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          Start Sequence
        </Button>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Queue Tabs */}
      <Tabs
        tabs={[
          { id: "due_today", label: "Due Today", icon: <AlertCircle className="h-4 w-4 text-rose-400" /> },
          { id: "upcoming", label: "Upcoming (7-14d)", icon: <Calendar className="h-4 w-4 text-sky-400" /> },
          { id: "waiting", label: "Waiting Reply", icon: <Clock className="h-4 w-4 text-amber-400" /> },
          { id: "completed", label: "Completed", icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" /> },
          { id: "stopped", label: "Stopped", icon: <StopCircle className="h-4 w-4 text-slate-400" /> },
        ]}
        activeTab={activeQueue}
        onChange={setActiveQueue}
      />

      {/* Follow-Up Items List */}
      <div className="space-y-4">
        {items.length === 0 ? (
          <Card glass className="p-8 text-center space-y-2">
            <Clock className="h-8 w-8 text-muted-foreground mx-auto" />
            <h4 className="text-sm font-bold text-foreground">No Follow-Ups in this Queue</h4>
            <p className="text-xs text-muted-foreground">
              {activeQueue === "due_today"
                ? "Awesome! No pending follow-ups due today."
                : "No follow-up items found matching the selected queue filter."}
            </p>
          </Card>
        ) : (
          items.map((item) => (
            <Card key={item.id} glass className="p-5 space-y-4 hover:border-amber-500/40 transition-all">
              {/* Card Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/50 pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 font-mono font-bold text-xs">
                    Step {item.stepNumber}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-foreground">{item.company} ({item.leadName})</h3>
                    <span className="text-[11px] text-muted-foreground font-mono">
                      Lead Stage: <span className="text-indigo-300 font-bold">{item.leadStatus}</span> • Due: {item.dueDate}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {getQueueBadge(item.status)}

                  {/* AI "Why should I follow up?" Button */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExplainWhy(item.id)}
                    isLoading={loadingAiId === item.id}
                    leftIcon={<HelpCircle className="h-3.5 w-3.5 text-purple-400" />}
                  >
                    Why Follow Up?
                  </Button>
                </div>
              </div>

              {/* AI Reasoning Rationale Card */}
              {item.aiReasoning && (
                <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-xs space-y-1 font-mono">
                  <span className="font-bold text-purple-300 flex items-center gap-1.5 text-[11px]">
                    <Sparkles className="h-3.5 w-3.5 text-purple-400" /> AI Follow-Up Rationale:
                  </span>
                  <p className="text-slate-200 text-[11px] leading-relaxed">{item.aiReasoning}</p>
                </div>
              )}

              {/* Draft Text Preview */}
              {item.draftBody ? (
                <div className="p-4 rounded-xl bg-card/60 border border-border/50 text-xs text-slate-200 font-mono whitespace-pre-wrap leading-relaxed">
                  {item.draftBody}
                </div>
              ) : (
                <div className="p-3 rounded-xl bg-card/40 border border-dashed border-border/60 text-[11px] text-muted-foreground flex items-center justify-between font-mono">
                  <span>No draft generated for Step {item.stepNumber} yet.</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleGenerateDraft(item.id)}
                    isLoading={loadingAiId === item.id}
                    leftIcon={<Sparkles className="h-3.5 w-3.5 text-sky-400" />}
                  >
                    Generate AI Draft
                  </Button>
                </div>
              )}

              {/* Action Buttons Bar */}
              <div className="pt-2 flex items-center justify-between border-t border-border/40">
                <span className="text-[10px] font-mono text-muted-foreground">
                  Cadence Delay: {item.delayDays} Days
                </span>

                <div className="flex items-center gap-2">
                  {item.status !== "STOPPED" && item.status !== "COMPLETED" && (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleStopSequence(item.id)}
                        leftIcon={<StopCircle className="h-3.5 w-3.5 text-rose-400" />}
                      >
                        Stop Cadence
                      </Button>

                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleSendFollowUp(item.id)}
                        leftIcon={<Send className="h-3.5 w-3.5" />}
                      >
                        Send Follow-Up
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* START SEQUENCE MODAL */}
      <Modal
        isOpen={isStartModalOpen}
        onClose={() => setIsStartModalOpen(false)}
        title="Initialize 3-Step Follow-Up Sequence"
      >
        <form onSubmit={handleStartSequence} className="space-y-4 text-xs">
          <div className="space-y-1">
            <label className="font-semibold text-foreground">Select Target Lead *</label>
            <select
              value={selectedLeadId}
              onChange={(e) => setSelectedLeadId(e.target.value)}
              className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
            >
              {leads.map((l) => (
                <option key={l.id} value={l.id}>{l.company} ({l.name})</option>
              ))}
            </select>
          </div>

          <div className="p-3.5 rounded-xl bg-secondary/40 border border-border/60 space-y-2 text-[11px] font-mono">
            <span className="font-bold text-foreground block">Cadence Schedule:</span>
            <ul className="space-y-1 text-muted-foreground">
              <li className="flex items-center gap-2"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Step 1: Follow-Up 1 after 3 Days</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Step 2: Follow-Up 2 after 7 Days</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Step 3: Final Follow-Up after 14 Days</li>
            </ul>
            <p className="text-amber-300 text-[10px] pt-1">
              * Sequence stops automatically if lead replies or stage moves to Meeting/Proposal/Won.
            </p>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" type="button" onClick={() => setIsStartModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isStarting}>
              Start Cadence
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
