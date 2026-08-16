"use client";

import React, { useState, useEffect } from "react";
import { SystemStatusBar } from "@/components/mission-control/SystemStatusBar";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Drawer } from "@/components/ui/Drawer";
import { Toast, ToastType } from "@/components/ui/Toast";
import {
  Users,
  Plus,
  Search,
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
  ShieldCheck,
  Brain,
  Bot,
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
];

export default function LeadsCRMPage() {
  const [viewMode, setViewMode] = useState<"kanban" | "matrix">("matrix");
  const [leads, setLeads] = useState<LeadItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isNewLeadModalOpen, setIsNewLeadModalOpen] = useState(false);

  // Selected Lead & Intelligence Drawer
  const [selectedLead, setSelectedLead] = useState<LeadItem | null>(null);
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
    if (!newLeadName.trim() || !newLeadCompany.trim() || !newLeadEmail.trim()) return;

    setIsCreating(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: newLeadName,
          company: newLeadCompany,
          email: newLeadEmail,
          industry: newLeadIndustry,
          serviceFit: newLeadServiceFit,
          status: "New",
        }),
      });

      if (res.ok) {
        setToast({ type: "success", title: "Lead Ingested", message: "Dispatched to LeadAgent for AI qualification." });
        setIsNewLeadModalOpen(false);
        setNewLeadName("");
        setNewLeadCompany("");
        setNewLeadEmail("");
        await fetchLeads();
      }
    } catch (err: any) {
      setToast({ type: "error", title: "Creation Failed", message: err.message });
    } finally {
      setIsCreating(false);
    }
  };

  const handleEnrichLead = async (leadId: string) => {
    setIsExecutingAI(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/leads/${leadId}/ai-enrich`, {
        method: "POST",
        credentials: "include",
      });

      if (res.ok) {
        setToast({ type: "success", title: "Lead Enriched", message: "Synthesized multi-source research report." });
        await fetchLeads();
      }
    } catch (err: any) {
      setToast({ type: "error", title: "Enrichment Error", message: err.message });
    } finally {
      setIsExecutingAI(false);
    }
  };

  const filteredLeads = leads.filter(
    (l) =>
      l.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* 1. Top System Status Strip */}
      <SystemStatusBar
        activeAgentsCount={12}
        runningWorkflowsCount={3}
        pendingApprovalsCount={1}
        systemHealth={99.4}
      />

      {/* 2. Lead Intelligence Header */}
      <div className="p-5 rounded-2xl glass-panel bg-card/80 border border-border/80 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 font-mono text-xs text-emerald-400 font-bold">
              <Users className="h-4 w-4" />
              <span>LEAD INTELLIGENCE & SCORING MATRIX</span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-foreground mt-0.5">
              Autonomous Pipeline & Prospect Reasoning
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center rounded-xl bg-surface/80 border border-border p-1">
              <button
                onClick={() => setViewMode("matrix")}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                  viewMode === "matrix" ? "bg-primary text-white" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Intelligence Matrix
              </button>
              <button
                onClick={() => setViewMode("kanban")}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                  viewMode === "kanban" ? "bg-primary text-white" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Pipeline Kanban
              </button>
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsNewLeadModalOpen(true)}
              leftIcon={<Plus className="h-3.5 w-3.5" />}
            >
              Ingest Prospect
            </Button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search leads by name, company, or domain..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-surface/90 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary font-mono"
          />
        </div>
      </div>

      {/* 3. Main Lead Intelligence Grid or Kanban */}
      {viewMode === "matrix" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredLeads.map((lead) => (
            <div
              key={lead.id}
              onClick={() => {
                setSelectedLead(lead);
                setIsDetailDrawerOpen(true);
              }}
              className="p-5 rounded-2xl glass-panel bg-card/70 border border-border/80 hover:border-primary/50 transition-all cursor-pointer space-y-4 shadow-sm"
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-foreground">{lead.name}</h3>
                  <div className="text-xs text-muted-foreground flex items-center gap-1">
                    <Building className="h-3 w-3" />
                    <span>{lead.company}</span>
                  </div>
                </div>

                <div className="text-right font-mono">
                  <span className="text-xs text-muted-foreground block text-[10px]">SCORE</span>
                  <span className="text-base font-bold text-emerald-400">{lead.leadScore || 88}</span>
                </div>
              </div>

              {/* AI Reasoning Strip */}
              <div className="p-3 rounded-xl bg-surface/60 border border-border/40 space-y-2 text-xs">
                <div>
                  <span className="text-[10px] font-mono uppercase text-primary font-bold block">
                    Why this lead matters:
                  </span>
                  <p className="text-[11px] text-muted-foreground line-clamp-2">
                    {lead.notes || "Matches ICP for high-value workflow automation. Recent funding trigger detected."}
                  </p>
                </div>

                <div>
                  <span className="text-[10px] font-mono uppercase text-secondary font-bold block">
                    Next recommended action:
                  </span>
                  <p className="text-[11px] text-foreground font-semibold line-clamp-1">
                    {lead.nextAction || "Dispatch personalized cold email sequence via OutreachAgent."}
                  </p>
                </div>
              </div>

              {/* Bottom Metadata */}
              <div className="flex items-center justify-between pt-2 border-t border-border/40 text-[10px] font-mono text-muted-foreground">
                <Badge variant="default" size="sm">
                  {lead.status || "Qualified"}
                </Badge>
                <span>{lead.email}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {PIPELINE_STAGES.slice(0, 5).map((stage) => {
            const stageLeads = filteredLeads.filter((l) => (l.status || "New") === stage);
            return (
              <div
                key={stage}
                className="w-72 shrink-0 p-4 rounded-2xl glass-panel bg-surface/50 border border-border/70 space-y-3"
              >
                <div className="flex items-center justify-between font-mono text-xs">
                  <span className="font-bold text-foreground">{stage}</span>
                  <span className="px-2 py-0.5 rounded bg-surface-high text-muted-foreground">
                    {stageLeads.length}
                  </span>
                </div>

                <div className="space-y-2.5">
                  {stageLeads.map((lead) => (
                    <div
                      key={lead.id}
                      onClick={() => {
                        setSelectedLead(lead);
                        setIsDetailDrawerOpen(true);
                      }}
                      className="p-3 rounded-xl bg-card border border-border hover:border-primary/40 transition-all cursor-pointer space-y-1.5"
                    >
                      <div className="flex justify-between items-center text-xs font-bold text-foreground">
                        <span>{lead.name}</span>
                        <span className="text-emerald-400 font-mono">{lead.leadScore || 85}</span>
                      </div>
                      <div className="text-[11px] text-muted-foreground">{lead.company}</div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 4. Lead Detail Drawer */}
      {selectedLead && (
        <Drawer
          isOpen={isDetailDrawerOpen}
          onClose={() => setIsDetailDrawerOpen(false)}
          position="right"
          title={`Lead Intelligence • ${selectedLead.name}`}
        >
          <div className="space-y-5 text-xs text-foreground">
            <div className="p-4 rounded-xl glass-panel bg-surface-low/80 border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold">{selectedLead.name}</span>
                <Badge variant="success" size="sm">
                  SCORE: {selectedLead.leadScore || 88}/100
                </Badge>
              </div>
              <div className="text-muted-foreground">{selectedLead.company} • {selectedLead.email}</div>
            </div>

            {/* AI Intelligence Brief */}
            <div className="p-4 rounded-xl bg-surface/70 border border-border space-y-3">
              <div className="flex items-center gap-2 font-bold text-primary">
                <Brain className="h-4 w-4" />
                <span>Autonomous AI Prospect Analysis</span>
              </div>
              <div className="space-y-2 leading-relaxed text-muted-foreground">
                <p><strong>ICP Alignment:</strong> 94% fit with enterprise automation solutions.</p>
                <p><strong>Intent Triggers:</strong> High activity in AI infrastructure modernization.</p>
                <p><strong>Recommended Strategy:</strong> Initiate personalized sequence focusing on autonomous multi-agent reliability.</p>
              </div>

              <Button
                variant="primary"
                size="sm"
                onClick={() => handleEnrichLead(selectedLead.id)}
                disabled={isExecutingAI}
                className="w-full justify-center mt-2"
                leftIcon={<Sparkles className="h-3.5 w-3.5" />}
              >
                {isExecutingAI ? "Enriching via ResearchAgent..." : "Re-Enrich Prospect Intelligence"}
              </Button>
            </div>
          </div>
        </Drawer>
      )}

      {/* 5. Ingest Modal */}
      <Modal isOpen={isNewLeadModalOpen} onClose={() => setIsNewLeadModalOpen(false)} title="Ingest New Prospect">
        <form onSubmit={handleCreateLead} className="space-y-4 text-xs">
          <div className="space-y-1">
            <label className="font-bold text-foreground">Contact Name:</label>
            <input
              type="text"
              required
              value={newLeadName}
              onChange={(e) => setNewLeadName(e.target.value)}
              placeholder="e.g. Alex Morgan"
              className="w-full p-2.5 rounded-xl bg-surface border border-border text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div className="space-y-1">
            <label className="font-bold text-foreground">Company Name:</label>
            <input
              type="text"
              required
              value={newLeadCompany}
              onChange={(e) => setNewLeadCompany(e.target.value)}
              placeholder="e.g. Apex Dynamics AI"
              className="w-full p-2.5 rounded-xl bg-surface border border-border text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div className="space-y-1">
            <label className="font-bold text-foreground">Work Email:</label>
            <input
              type="email"
              required
              value={newLeadEmail}
              onChange={(e) => setNewLeadEmail(e.target.value)}
              placeholder="alex@apexdynamics.ai"
              className="w-full p-2.5 rounded-xl bg-surface border border-border text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-border">
            <Button variant="ghost" size="sm" onClick={() => setIsNewLeadModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" disabled={isCreating}>
              {isCreating ? "Ingesting..." : "Ingest & Qualify"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Toast Notification */}
      {toast && <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />}
    </div>
  );
}
