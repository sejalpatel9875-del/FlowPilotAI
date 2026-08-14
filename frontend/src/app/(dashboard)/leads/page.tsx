"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Drawer } from "@/components/ui/Drawer";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Tabs } from "@/components/ui/Tabs";
import {
  Users,
  Plus,
  Search,
  Filter,
  Kanban,
  Table as TableIcon,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  Eye,
  Trash2,
  Building,
  Globe,
  MapPin,
  Mail,
  Send,
  Target,
  BarChart2,
  ShieldCheck
} from "lucide-react";

interface LeadItem {
  id: string;
  name: string;
  company: string;
  email: string;
  website: string;
  industry: string;
  location: string;
  source: string;
  serviceFit: string;
  leadScore: number;
  status: string;
  notes?: string;
  nextAction?: string;
  verificationStatus: "Verified" | "Inferred" | "Unknown";
  createdAt: string;
}

const PIPELINE_STAGES = [
  "New",
  "Qualified",
  "Researching",
  "Outreach Ready",
  "Contacted",
  "Replied",
  "Meeting",
  "Proposal",
  "Won",
  "Lost",
  "Not Interested"
];

export default function LeadsCRMPage() {
  const [viewMode, setViewMode] = useState<"kanban" | "table">("kanban");
  const [leads, setLeads] = useState<LeadItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isNewLeadModalOpen, setIsNewLeadModalOpen] = useState(false);

  // Lead Detail State
  const [selectedLeadDetail, setSelectedLeadDetail] = useState<any>(null);
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState(false);
  const [isExecutingAI, setIsExecutingAI] = useState(false);

  // New Lead Form State
  const [newLeadName, setNewLeadName] = useState("");
  const [newLeadCompany, setNewLeadCompany] = useState("");
  const [newLeadEmail, setNewLeadEmail] = useState("");
  const [newLeadIndustry, setNewLeadIndustry] = useState("Technology");
  const [newLeadServiceFit, setNewLeadServiceFit] = useState("High");
  const [isCreating, setIsCreating] = useState(false);

  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/leads", {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setLeads(data.leads || []);
      }
    } catch (err) {
      console.error("Failed to load leads", err);
    }
  };

  const handleCreateLead = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLeadCompany || !newLeadEmail) return;

    setIsCreating(true);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: newLeadName || newLeadCompany,
          company: newLeadCompany,
          email: newLeadEmail,
          industry: newLeadIndustry,
          serviceFit: newLeadServiceFit,
          status: "New",
          verificationStatus: "Verified",
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to create lead.");
      }

      const newLead = await res.json();
      setToast({ type: "success", title: "Lead Ingested", message: `Added '${newLead.company}' to CRM with score ${newLead.leadScore}.` });
      setIsNewLeadModalOpen(false);
      setNewLeadName("");
      setNewLeadCompany("");
      setNewLeadEmail("");
      fetchLeads();
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    } finally {
      setIsCreating(false);
    }
  };

  const handleOpenDetail = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/leads/${id}`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedLeadDetail(data);
        setIsDetailDrawerOpen(true);
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to load lead details." });
    }
  };

  const handleUpdateStatus = async (leadId: string, newStatus: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/leads/${leadId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        setToast({ type: "success", title: "Stage Updated", message: `Moved lead stage to '${newStatus}'.` });
        fetchLeads();
        if (selectedLeadDetail && selectedLeadDetail.id === leadId) {
          handleOpenDetail(leadId);
        }
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to update status." });
    }
  };

  const handleRunAIAction = async (leadId: string, actionType: string) => {
    setIsExecutingAI(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/leads/${leadId}/ai-action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ actionType }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "AI action execution failed.");
      }

      const data = await res.json();
      setToast({ type: "success", title: "AI Action Completed", message: `Executed '${actionType}' for ${data.company}.` });
      fetchLeads();
      handleOpenDetail(leadId);
    } catch (err: any) {
      setToast({ type: "error", title: "AI Execution Failed", message: err.message });
    } finally {
      setIsExecutingAI(false);
    }
  };

  const getVerificationBadge = (v: string) => {
    switch (v) {
      case "Verified": return <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono font-bold text-[9px]">VERIFIED</span>;
      case "Inferred": return <span className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono font-bold text-[9px]">INFERRED</span>;
      default: return <span className="px-2 py-0.5 rounded-md bg-slate-500/20 text-slate-300 border border-slate-500/30 font-mono font-bold text-[9px]">UNKNOWN</span>;
    }
  };

  const filteredLeads = leads.filter(
    (l) =>
      l.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.industry.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Users className="h-6 w-6 text-emerald-400" />
            Lead Generation CRM
          </h1>
          <p className="text-xs text-muted-foreground">
            11-stage sales pipeline with transparent lead scoring and automated AI actions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Mode Switcher */}
          <div className="flex items-center rounded-xl glass-panel p-1 bg-secondary/30 border border-border/60">
            <button
              onClick={() => setViewMode("kanban")}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === "kanban" ? "bg-primary text-white shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Kanban className="h-3.5 w-3.5" /> Kanban
            </button>
            <button
              onClick={() => setViewMode("table")}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === "table" ? "bg-primary text-white shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <TableIcon className="h-3.5 w-3.5" /> Table
            </button>
          </div>

          <Button
            variant="primary"
            size="md"
            onClick={() => setIsNewLeadModalOpen(true)}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Add Lead
          </Button>
        </div>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Search Bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search leads by company, contact name, or industry..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-panel bg-secondary/30 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/60"
          />
        </div>
      </div>

      {/* VIEW MODE 1: KANBAN BOARD (11 PIPELINE STAGES) */}
      {viewMode === "kanban" && (
        <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin">
          {PIPELINE_STAGES.map((stage) => {
            const stageLeads = filteredLeads.filter((l) => l.status === stage);
            return (
              <div key={stage} className="w-72 shrink-0 space-y-3">
                {/* Column Header */}
                <div className="flex items-center justify-between p-3 rounded-xl glass-panel bg-secondary/40 border border-border/60">
                  <span className="text-xs font-bold text-foreground">{stage}</span>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-card text-muted-foreground border border-border/40">
                    {stageLeads.length}
                  </span>
                </div>

                {/* Column Lead Cards */}
                <div className="space-y-3 min-h-[400px]">
                  {stageLeads.map((lead) => (
                    <Card
                      key={lead.id}
                      glass
                      className="p-4 space-y-3 hover:border-primary/40 transition-all cursor-pointer"
                      onClick={() => handleOpenDetail(lead.id)}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h4 className="text-sm font-bold text-foreground">{lead.company}</h4>
                          <span className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                            <Mail className="h-3 w-3 text-indigo-400" /> {lead.name}
                          </span>
                        </div>

                        <div className="flex flex-col items-end">
                          <span className="text-xs font-mono font-bold text-emerald-400">{lead.leadScore} Score</span>
                          {getVerificationBadge(lead.verificationStatus)}
                        </div>
                      </div>

                      {/* Next Action Pill */}
                      {lead.nextAction && (
                        <div className="p-2 rounded-lg bg-card/60 border border-border/40 text-[10px] font-mono text-muted-foreground flex items-center justify-between">
                          <span className="truncate">🎯 {lead.nextAction}</span>
                        </div>
                      )}

                      {/* Stage Selector & Quick Actions */}
                      <div className="pt-2 border-t border-border/40 flex items-center justify-between" onClick={(e) => e.stopPropagation()}>
                        <select
                          value={lead.status}
                          onChange={(e) => handleUpdateStatus(lead.id, e.target.value)}
                          className="rounded-lg bg-card px-2 py-1 text-[10px] font-mono text-foreground border border-border/60"
                        >
                          {PIPELINE_STAGES.map((s) => (
                            <option key={s} value={s}>{s}</option>
                          ))}
                        </select>

                        <button
                          onClick={() => handleOpenDetail(lead.id)}
                          className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
                          title="View Details"
                        >
                          <Eye className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* VIEW MODE 2: TABLE VIEW */}
      {viewMode === "table" && (
        <Card glass>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="border-b border-border/60 text-muted-foreground bg-muted/20">
                  <tr>
                    <th className="py-3 px-4 font-semibold">Company</th>
                    <th className="py-3 px-4 font-semibold">Contact</th>
                    <th className="py-3 px-4 font-semibold">Industry</th>
                    <th className="py-3 px-4 font-semibold">Score</th>
                    <th className="py-3 px-4 font-semibold">Stage</th>
                    <th className="py-3 px-4 font-semibold">Verification</th>
                    <th className="py-3 px-4 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {filteredLeads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-muted/30 cursor-pointer" onClick={() => handleOpenDetail(lead.id)}>
                      <td className="py-3 px-4 font-bold text-foreground">{lead.company}</td>
                      <td className="py-3 px-4 text-muted-foreground">{lead.name} ({lead.email})</td>
                      <td className="py-3 px-4 text-muted-foreground">{lead.industry}</td>
                      <td className="py-3 px-4 font-bold text-emerald-400">{lead.leadScore}/100</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20 text-[10px]">
                          {lead.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">{getVerificationBadge(lead.verificationStatus)}</td>
                      <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button variant="outline" size="sm" onClick={() => handleOpenDetail(lead.id)}>
                          View Details
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* NEW LEAD MODAL */}
      <Modal
        isOpen={isNewLeadModalOpen}
        onClose={() => setIsNewLeadModalOpen(false)}
        title="Ingest New Prospect Lead"
      >
        <form onSubmit={handleCreateLead} className="space-y-4 text-xs">
          <div className="space-y-1">
            <label className="font-semibold text-foreground">Company Name *</label>
            <input
              type="text"
              required
              placeholder="e.g. Acme Corp"
              value={newLeadCompany}
              onChange={(e) => setNewLeadCompany(e.target.value)}
              className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
            />
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-foreground">Contact Email *</label>
            <input
              type="email"
              required
              placeholder="e.g. alex@acme.com"
              value={newLeadEmail}
              onChange={(e) => setNewLeadEmail(e.target.value)}
              className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
            />
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-foreground">Contact Person Name</label>
            <input
              type="text"
              placeholder="e.g. Alex Rivera"
              value={newLeadName}
              onChange={(e) => setNewLeadName(e.target.value)}
              className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="font-semibold text-foreground">Industry</label>
              <input
                type="text"
                value={newLeadIndustry}
                onChange={(e) => setNewLeadIndustry(e.target.value)}
                className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
              />
            </div>
            <div className="space-y-1">
              <label className="font-semibold text-foreground">Service Fit</label>
              <select
                value={newLeadServiceFit}
                onChange={(e) => setNewLeadServiceFit(e.target.value)}
                className="w-full rounded-xl glass-panel bg-secondary/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
              >
                <option value="High">High Fit</option>
                <option value="Medium">Medium Fit</option>
                <option value="Low">Low Fit</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" type="button" onClick={() => setIsNewLeadModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isCreating}>
              Ingest & Score Lead
            </Button>
          </div>
        </form>
      </Modal>

      {/* LEAD DETAIL DRAWER WITH TRANSPARENT SCORING & AI ACTIONS */}
      <Drawer
        isOpen={isDetailDrawerOpen}
        onClose={() => setIsDetailDrawerOpen(false)}
        title={selectedLeadDetail ? `${selectedLeadDetail.company} (${selectedLeadDetail.name})` : "Lead Details"}
      >
        {selectedLeadDetail && (
          <div className="space-y-6 text-xs">
            {/* Header Metrics */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-card border border-border/50">
              <div>
                <span className="text-muted-foreground block text-[10px]">Overall Lead Score</span>
                <span className="text-xl font-bold text-emerald-400 font-mono">{selectedLeadDetail.leadScore}/100</span>
              </div>
              <div>
                <span className="text-muted-foreground block text-[10px]">Fact Verification</span>
                {getVerificationBadge(selectedLeadDetail.verificationStatus)}
              </div>
              <div>
                <span className="text-muted-foreground block text-[10px]">Pipeline Stage</span>
                <span className="font-bold text-indigo-300">{selectedLeadDetail.status}</span>
              </div>
            </div>

            {/* AI Action Trigger Buttons */}
            <div className="space-y-2">
              <span className="font-semibold text-foreground block text-[11px]">Automated AI Actions</span>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleRunAIAction(selectedLeadDetail.id, "analyze")}
                  isLoading={isExecutingAI}
                  leftIcon={<Sparkles className="h-3.5 w-3.5 text-purple-400" />}
                >
                  Analyze Lead
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleRunAIAction(selectedLeadDetail.id, "opportunity")}
                  isLoading={isExecutingAI}
                  leftIcon={<Target className="h-3.5 w-3.5 text-sky-400" />}
                >
                  Find Opportunity
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleRunAIAction(selectedLeadDetail.id, "outreach")}
                  isLoading={isExecutingAI}
                  leftIcon={<Send className="h-3.5 w-3.5 text-emerald-400" />}
                >
                  Generate Outreach
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleRunAIAction(selectedLeadDetail.id, "recommend_next_action")}
                  isLoading={isExecutingAI}
                  leftIcon={<ArrowRight className="h-3.5 w-3.5 text-amber-400" />}
                >
                  Recommend Action
                </Button>
              </div>
            </div>

            {/* Transparent Score Breakdown Meter */}
            {selectedLeadDetail.scoreBreakdown && (
              <div className="space-y-3 p-4 rounded-xl glass-panel bg-secondary/30 border border-border/60">
                <h4 className="font-bold text-foreground flex items-center gap-2">
                  <BarChart2 className="h-4 w-4 text-indigo-400" />
                  Transparent Score Factor Breakdown
                </h4>
                <div className="space-y-2 text-[11px] font-mono">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Service Fit (Max 25):</span>
                    <span className="text-emerald-400 font-bold">{selectedLeadDetail.scoreBreakdown.serviceFitScore} pts</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Industry Alignment (Max 20):</span>
                    <span className="text-emerald-400 font-bold">{selectedLeadDetail.scoreBreakdown.industryFitScore} pts</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Opportunity Signals (Max 25):</span>
                    <span className="text-emerald-400 font-bold">{selectedLeadDetail.scoreBreakdown.opportunitySignalsScore} pts</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Project Potential (Max 15):</span>
                    <span className="text-emerald-400 font-bold">{selectedLeadDetail.scoreBreakdown.projectPotentialScore} pts</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Verified Contact Info (Max 15):</span>
                    <span className="text-emerald-400 font-bold">{selectedLeadDetail.scoreBreakdown.contactInfoScore} pts</span>
                  </div>
                </div>
              </div>
            )}

            {/* Profile Info */}
            <div className="space-y-2 p-3.5 rounded-xl bg-card border border-border/50 text-[11px]">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Email:</span>
                <span className="text-foreground font-semibold">{selectedLeadDetail.email}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Industry:</span>
                <span className="text-foreground font-semibold">{selectedLeadDetail.industry}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Location:</span>
                <span className="text-foreground font-semibold">{selectedLeadDetail.location}</span>
              </div>
            </div>

            {/* Activity Timeline */}
            <div className="space-y-3">
              <h4 className="font-bold text-foreground">Audited Activity Timeline ({selectedLeadDetail.activities?.length || 0})</h4>
              <div className="space-y-2">
                {selectedLeadDetail.activities?.map((act: any) => (
                  <div key={act.id} className="p-3 rounded-xl glass-panel bg-secondary/30 border border-border/60 text-[11px] space-y-1">
                    <div className="flex items-center justify-between text-indigo-300 font-mono font-bold">
                      <span className="uppercase">{act.type}</span>
                      <span className="text-muted-foreground text-[10px]">{act.timestamp}</span>
                    </div>
                    <p className="text-slate-200">{act.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}
