"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Tabs } from "@/components/ui/Tabs";
import {
  Send,
  Mail,
  Linkedin,
  FileText,
  MessageSquare,
  CheckCircle2,
  XCircle,
  Clock,
  Edit3,
  Calendar,
  Sparkles,
  ShieldAlert,
  Inbox,
  Filter,
  Check,
  X,
  Play
} from "lucide-react";

interface OutreachItem {
  id: string;
  leadId: string;
  leadCompany: string;
  leadName: string;
  leadEmail: string;
  channel: string;
  subject?: string;
  draftBody: string;
  status: "DRAFT" | "REVIEW" | "APPROVED" | "SCHEDULED" | "SENT" | "FAILED" | "CANCELLED";
  scheduledAt?: string;
  approvedAt?: string;
  sentAt?: string;
  createdAt: string;
}

interface LeadItem {
  id: string;
  company: string;
  name: string;
}

export default function OutreachApprovalInboxPage() {
  const [activeTab, setActiveTab] = useState("review");
  const [channelFilter, setChannelFilter] = useState<string>("ALL");
  const [messages, setMessages] = useState<OutreachItem[]>([]);
  const [leads, setLeads] = useState<LeadItem[]>([]);

  // Modals
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [selectedLeadId, setSelectedLeadId] = useState("");
  const [selectedChannel, setSelectedChannel] = useState("Email");
  const [customPrompt, setCustomPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // Edit Modal
  const [editingMessage, setEditingMessage] = useState<OutreachItem | null>(null);
  const [editSubject, setEditSubject] = useState("");
  const [editBody, setEditBody] = useState("");
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchOutreachData();
    fetchLeads();
  }, []);

  const fetchOutreachData = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/outreach", {
        credentials: "include",
      });
      if (res.ok) {
        setMessages((await res.json()).messages || []);
      }
    } catch (err) {
      console.error("Failed to load outreach messages", err);
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

  const handleGenerateDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLeadId) return;

    setIsGenerating(true);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/outreach/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          leadId: selectedLeadId,
          channel: selectedChannel,
          customInstructions: customPrompt,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Draft generation failed.");
      }

      const data = await res.json();
      setToast({ type: "success", title: "Outreach Draft Generated", message: data.message });
      setIsGenerateModalOpen(false);
      fetchOutreachData();
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/outreach/${id}/approve`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        setToast({ type: "success", title: "Message Approved", message: "Draft approved and ready for delivery." });
        fetchOutreachData();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to approve message." });
    }
  };

  const handleReject = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/outreach/${id}/reject`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        setToast({ type: "warning", title: "Message Cancelled", message: "Draft moved to cancelled status." });
        fetchOutreachData();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to reject message." });
    }
  };

  const handleSendNow = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/outreach/${id}/send`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        setToast({ type: "success", title: "Outreach Dispatched", message: "Message sent and lead stage updated to Contacted." });
        fetchOutreachData();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to send message." });
    }
  };

  const handleOpenEdit = (msg: OutreachItem) => {
    setEditingMessage(msg);
    setEditSubject(msg.subject || "");
    setEditBody(msg.draftBody);
  };

  const handleSaveEdit = async () => {
    if (!editingMessage) return;
    setIsSavingEdit(true);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/outreach/${editingMessage.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          subject: editSubject,
          draftBody: editBody,
        }),
      });

      if (res.ok) {
        setToast({ type: "success", title: "Draft Updated", message: "Edits saved successfully." });
        setEditingMessage(null);
        fetchOutreachData();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to save edits." });
    } finally {
      setIsSavingEdit(false);
    }
  };

  const getChannelIcon = (ch: string) => {
    switch (ch) {
      case "Email": return <Mail className="h-4 w-4 text-sky-400" />;
      case "LinkedIn connection note": return <Linkedin className="h-4 w-4 text-blue-400" />;
      case "Freelance proposal": return <FileText className="h-4 w-4 text-purple-400" />;
      default: return <MessageSquare className="h-4 w-4 text-emerald-400" />;
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case "REVIEW": return <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono font-bold text-[10px]">PENDING REVIEW</span>;
      case "APPROVED": return <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono font-bold text-[10px]">APPROVED</span>;
      case "SCHEDULED": return <span className="px-2.5 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30 font-mono font-bold text-[10px]">SCHEDULED</span>;
      case "SENT": return <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono font-bold text-[10px]">SENT</span>;
      case "CANCELLED": return <span className="px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono font-bold text-[10px]">CANCELLED</span>;
      default: return <span className="px-2.5 py-0.5 rounded-full bg-slate-500/20 text-slate-300 border border-slate-500/30 font-mono font-bold text-[10px]">{st}</span>;
    }
  };

  const filteredMessages = messages.filter((m) => {
    if (channelFilter !== "ALL" && m.channel !== channelFilter) return false;
    if (activeTab === "review") return m.status === "REVIEW";
    if (activeTab === "approved") return m.status === "APPROVED" || m.status === "SCHEDULED";
    if (activeTab === "sent") return m.status === "SENT";
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Send className="h-6 w-6 text-sky-400" />
            Outreach & Human Approval Inbox
          </h1>
          <p className="text-xs text-muted-foreground">
            Personalized AI drafts across Email, LinkedIn, Proposals, and Contact Forms. No automated mass-sending.
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={() => setIsGenerateModalOpen(true)}
          leftIcon={<Sparkles className="h-4 w-4 text-purple-400" />}
        >
          Draft New Outreach
        </Button>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Channel Filters */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <span className="text-xs text-muted-foreground font-mono flex items-center gap-1 mr-2">
          <Filter className="h-3.5 w-3.5" /> Channel:
        </span>
        {["ALL", "Email", "LinkedIn connection note", "Freelance proposal", "Contact form draft"].map((ch) => (
          <button
            key={ch}
            onClick={() => setChannelFilter(ch)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              channelFilter === ch
                ? "bg-primary text-white shadow-sm"
                : "glass-panel bg-secondary/30 text-muted-foreground hover:text-foreground"
            }`}
          >
            {ch === "ALL" ? "All Channels" : ch}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: "review", label: `Pending Review (${messages.filter((m) => m.status === "REVIEW").length})`, icon: <Inbox className="h-4 w-4 text-amber-400" /> },
          { id: "approved", label: `Approved & Scheduled (${messages.filter((m) => m.status === "APPROVED" || m.status === "SCHEDULED").length})`, icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" /> },
          { id: "sent", label: `Sent History (${messages.filter((m) => m.status === "SENT").length})`, icon: <Send className="h-4 w-4 text-sky-400" /> },
          { id: "all", label: `All Messages (${messages.length})`, icon: <FileText className="h-4 w-4" /> },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {/* Messages List */}
      <div className="space-y-4">
        {filteredMessages.length === 0 ? (
          <Card glass className="p-8 text-center space-y-2">
            <Inbox className="h-8 w-8 text-muted-foreground mx-auto" />
            <h4 className="text-sm font-bold text-foreground">No Outreach Messages Found</h4>
            <p className="text-xs text-muted-foreground">
              {activeTab === "review"
                ? "All outreach drafts have been reviewed! Click 'Draft New Outreach' to generate AI copy."
                : "No messages matching selected filters."}
            </p>
          </Card>
        ) : (
          filteredMessages.map((msg) => (
            <Card key={msg.id} glass className="p-5 space-y-4 hover:border-sky-500/40 transition-all">
              {/* Message Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/50 pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-secondary/50 border border-border/60">
                    {getChannelIcon(msg.channel)}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-foreground">{msg.leadCompany} ({msg.leadName})</h3>
                    <span className="text-[11px] text-muted-foreground font-mono">{msg.channel} • {msg.leadEmail}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {getStatusBadge(msg.status)}
                  <span className="text-[10px] text-muted-foreground font-mono">{msg.createdAt}</span>
                </div>
              </div>

              {/* Subject */}
              {msg.subject && (
                <div className="text-xs font-bold text-foreground flex items-center gap-2">
                  <span className="text-muted-foreground text-[10px] font-mono">Subject:</span>
                  <span>{msg.subject}</span>
                </div>
              )}

              {/* Body Content */}
              <div className="p-4 rounded-xl bg-card/60 border border-border/50 text-xs text-slate-200 font-mono whitespace-pre-wrap leading-relaxed">
                {msg.draftBody}
              </div>

              {/* Action Buttons Bar */}
              <div className="pt-2 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleOpenEdit(msg)} leftIcon={<Edit3 className="h-3.5 w-3.5 text-indigo-400" />}>
                    Edit Draft
                  </Button>
                </div>

                <div className="flex items-center gap-2">
                  {msg.status === "REVIEW" && (
                    <>
                      <Button variant="outline" size="sm" onClick={() => handleReject(msg.id)} leftIcon={<X className="h-3.5 w-3.5 text-rose-400" />}>
                        Reject
                      </Button>
                      <Button variant="primary" size="sm" onClick={() => handleApprove(msg.id)} leftIcon={<Check className="h-3.5 w-3.5 text-emerald-400" />}>
                        Approve Message
                      </Button>
                    </>
                  )}

                  {msg.status === "APPROVED" && (
                    <Button variant="primary" size="sm" onClick={() => handleSendNow(msg.id)} leftIcon={<Send className="h-3.5 w-3.5" />}>
                      Send Now
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* GENERATE DRAFT MODAL */}
      <Modal
        isOpen={isGenerateModalOpen}
        onClose={() => setIsGenerateModalOpen(false)}
        title="Generate Personalized Outreach Draft"
      >
        <form onSubmit={handleGenerateDraft} className="space-y-4 text-xs">
          <div className="space-y-1">
            <label className="font-semibold text-foreground">Target Qualified Lead *</label>
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

          <div className="space-y-1">
            <label className="font-semibold text-foreground">Outreach Channel *</label>
            <select
              value={selectedChannel}
              onChange={(e) => setSelectedChannel(e.target.value)}
              className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
            >
              <option value="Email">Email</option>
              <option value="LinkedIn connection note">LinkedIn Connection Note</option>
              <option value="Freelance proposal">Freelance Proposal</option>
              <option value="Contact form draft">Contact Form Draft</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-foreground">Custom Instructions (Optional)</label>
            <textarea
              rows={3}
              placeholder="e.g. Highlight our past React/Python deliverables and offer a 15-min discovery call."
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              className="w-full rounded-xl glass-panel bg-secondary/40 p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" type="button" onClick={() => setIsGenerateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isGenerating}>
              Generate Draft
            </Button>
          </div>
        </form>
      </Modal>

      {/* EDIT DRAFT MODAL */}
      {editingMessage && (
        <Modal
          isOpen={!!editingMessage}
          onClose={() => setEditingMessage(null)}
          title={`Edit ${editingMessage.channel} Draft`}
        >
          <div className="space-y-4 text-xs">
            {editingMessage.subject !== undefined && (
              <div className="space-y-1">
                <label className="font-semibold text-foreground">Subject Line</label>
                <input
                  type="text"
                  value={editSubject}
                  onChange={(e) => setEditSubject(e.target.value)}
                  className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 font-mono"
                />
              </div>
            )}

            <div className="space-y-1">
              <label className="font-semibold text-foreground">Message Body</label>
              <textarea
                rows={8}
                value={editBody}
                onChange={(e) => setEditBody(e.target.value)}
                className="w-full rounded-xl glass-panel bg-secondary/40 p-3 text-xs text-slate-200 font-mono focus:outline-none focus:ring-2 focus:ring-primary border-border/80 resize-none leading-relaxed"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setEditingMessage(null)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleSaveEdit} isLoading={isSavingEdit}>
                Save Edits
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
