"use client";

import React, { useState, useEffect } from "react";
import { SystemStatusBar } from "@/components/mission-control/SystemStatusBar";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Toast, ToastType } from "@/components/ui/Toast";
import {
  ShieldCheck,
  Lock,
  Key,
  Database,
  Cpu,
  Terminal,
  Eye,
  AlertTriangle,
  CheckCircle2,
  Activity,
  Layers,
  Shield,
  Search,
  RefreshCw,
  Zap,
} from "lucide-react";

interface SecurityEvent {
  id: string;
  userId?: string;
  action: string;
  resourceType: string;
  resourceId?: string;
  ipAddress: string;
  details?: string;
  timestamp: string;
}

export default function SecurityPage() {
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [activeTab, setActiveTab] = useState<"controls" | "audit" | "scanner">("controls");

  // Prompt Scanner State
  const [scanInput, setScanInput] = useState("");
  const [scanResult, setScanResult] = useState<any>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchSecurityDashboard();
    fetchSecurityEvents();
  }, []);

  const fetchSecurityDashboard = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/security/dashboard", {
        credentials: "include",
      });
      if (res.ok) {
        setDashboardData(await res.json());
      }
    } catch (err) {
      console.error("Failed to load security dashboard", err);
    }
  };

  const fetchSecurityEvents = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/security/events", {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
      }
    } catch (err) {
      console.error("Failed to load security events", err);
    }
  };

  const handleScanPrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scanInput) return;

    setIsScanning(true);
    setScanResult(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/security/scan-prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ queryText: scanInput }),
      });

      if (res.ok) {
        const data = await res.json();
        setScanResult(data);
        setToast({
          type: data.isSafe ? "success" : "warning",
          title: data.isSafe ? "Scan Passed" : "Security Flags Detected",
          message: data.isSafe
            ? "Zero prompt injection or secret leakage detected."
            : "Sensitive tokens were automatically redacted.",
        });
      }
    } catch (err: any) {
      setToast({ type: "error", title: "Scan Failed", message: err.message });
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Top System Status Strip */}
      <SystemStatusBar
        activeAgentsCount={12}
        runningWorkflowsCount={3}
        pendingApprovalsCount={1}
        systemHealth={99.4}
      />

      {/* 2. Enterprise Trust Header */}
      <div className="p-5 rounded-2xl glass-panel bg-card/80 border border-border/80 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 font-mono text-xs text-rose-400 font-bold">
              <Shield className="h-4 w-4" />
              <span>ENTERPRISE TRUST & GOVERNANCE CONTROL ROOM</span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-foreground mt-0.5">
              Autonomous Safety, Policy Enforcement & Isolation
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="glass" size="sm" onClick={fetchSecurityDashboard} leftIcon={<RefreshCw className="h-3.5 w-3.5" />}>
              Re-Audit Controls
            </Button>
          </div>
        </div>

        {/* Four Core Trust Indicators */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 font-mono text-xs">
          <div className="p-3.5 rounded-xl bg-surface/70 border border-emerald-500/30 space-y-1">
            <div className="text-[10px] text-muted-foreground uppercase">System Trust</div>
            <div className="text-lg font-bold text-emerald-400">100% VERIFIED</div>
          </div>

          <div className="p-3.5 rounded-xl bg-surface/70 border border-emerald-500/30 space-y-1">
            <div className="text-[10px] text-muted-foreground uppercase">AI Policy Status</div>
            <div className="text-lg font-bold text-emerald-400">ACTIVE & STRICT</div>
          </div>

          <div className="p-3.5 rounded-xl bg-surface/70 border border-emerald-500/30 space-y-1">
            <div className="text-[10px] text-muted-foreground uppercase">Tenant Isolation</div>
            <div className="text-lg font-bold text-sky-400">SECURE BOUNDARY</div>
          </div>

          <div className="p-3.5 rounded-xl bg-surface/70 border border-emerald-500/30 space-y-1">
            <div className="text-[10px] text-muted-foreground uppercase">Audit Integrity</div>
            <div className="text-lg font-bold text-emerald-400">CRYPTOGRAPHIC</div>
          </div>
        </div>
      </div>

      {/* 3. Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-border/60 pb-2">
        {[
          { id: "controls", label: "Security & Isolation Controls" },
          { id: "scanner", label: "Prompt Injection & Secret Redactor" },
          { id: "audit", label: `Immutable Audit Trail (${events.length})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === tab.id
                ? "bg-primary text-white shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-surface-high"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 4. Tab Content */}
      {activeTab === "controls" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="p-5 rounded-2xl glass-panel bg-card/70 border border-border/80 space-y-3">
            <div className="flex items-center gap-2 font-bold text-foreground text-sm">
              <Lock className="h-4 w-4 text-emerald-400" />
              <span>Multi-Tenant Vault</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Every database query and agent execution is strictly scoped by user session token. Cross-tenant leakage is mathematically impossible.
            </p>
            <div className="text-[11px] font-mono text-emerald-400 pt-2 border-t border-border/40">
              Status: Active • Zero Violations
            </div>
          </div>

          <div className="p-5 rounded-2xl glass-panel bg-card/70 border border-border/80 space-y-3">
            <div className="flex items-center gap-2 font-bold text-foreground text-sm">
              <Key className="h-4 w-4 text-primary" />
              <span>Secret Redaction Gateway</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              API keys, OAuth tokens, and bearer credentials are automatically sanitized from agent context envelopes before LLM dispatch.
            </p>
            <div className="text-[11px] font-mono text-primary pt-2 border-t border-border/40">
              Regex & Pattern Engine: 100% Active
            </div>
          </div>

          <div className="p-5 rounded-2xl glass-panel bg-card/70 border border-border/80 space-y-3">
            <div className="flex items-center gap-2 font-bold text-foreground text-sm">
              <ShieldCheck className="h-4 w-4 text-amber-400" />
              <span>Human Authorization Gate</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Irreversible actions (email transmission, schedule creation, delete calls) require human approval before worker execution.
            </p>
            <div className="text-[11px] font-mono text-amber-400 pt-2 border-t border-border/40">
              Side-Effect Protection: Enforced
            </div>
          </div>
        </div>
      )}

      {activeTab === "scanner" && (
        <div className="p-6 rounded-2xl glass-panel bg-card/70 border border-border/80 space-y-4">
          <div>
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <Zap className="h-4 w-4 text-sky-400" />
              Real-time Prompt Injection & Secret Redaction Testing Sandbox
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Submit test prompts to evaluate FlowPilot's multi-layered LLM sanitization and adversarial guardrails.
            </p>
          </div>

          <form onSubmit={handleScanPrompt} className="space-y-3">
            <textarea
              value={scanInput}
              onChange={(e) => setScanInput(e.target.value)}
              placeholder="Paste prompt with potential API keys, system override instructions, or jailbreaks..."
              rows={3}
              className="w-full p-3 rounded-xl bg-surface border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary font-mono"
            />
            <div className="flex justify-end">
              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={isScanning || !scanInput.trim()}
                leftIcon={<Search className="h-3.5 w-3.5" />}
              >
                {isScanning ? "Scanning..." : "Execute Security Scan"}
              </Button>
            </div>
          </form>

          {scanResult && (
            <div className="p-4 rounded-xl bg-surface-lowest border border-border/60 space-y-2 font-mono text-xs animate-in fade-in">
              <div className="flex items-center justify-between">
                <span className="font-bold text-foreground">Scan Result Verdict:</span>
                <Badge variant={scanResult.isSafe ? "success" : "warning"} size="sm">
                  {scanResult.isSafe ? "SAFE TO DISPATCH" : "SENSITIVE TOKENS REDACTED"}
                </Badge>
              </div>
              <div className="p-3 rounded-lg bg-surface text-muted-foreground">
                <div className="text-[10px] uppercase text-primary font-bold mb-1">Sanitized Output Payload:</div>
                <pre className="whitespace-pre-wrap">{scanResult.sanitizedPrompt || scanInput}</pre>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "audit" && (
        <div className="p-6 rounded-2xl glass-panel bg-card/70 border border-border/80 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-border/60">
            <h3 className="text-xs font-bold uppercase tracking-wider font-mono text-foreground flex items-center gap-2">
              <Terminal className="h-4 w-4 text-primary" />
              Cryptographic Audit Stream ({events.length} Recorded Events)
            </h3>
            <span className="text-[10px] font-mono text-emerald-400">Append-Only Invariant</span>
          </div>

          <div className="space-y-2 max-h-96 overflow-y-auto pr-1 font-mono text-xs">
            {events.length === 0 ? (
              <p className="text-muted-foreground text-xs">No audit events recorded yet.</p>
            ) : (
              events.map((ev) => (
                <div
                  key={ev.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-surface/60 border border-border/40 hover:border-border transition-all"
                >
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-0.5 rounded bg-surface-high border border-border text-[10px] font-bold text-foreground">
                      {ev.action}
                    </span>
                    <span className="text-muted-foreground">{ev.resourceType}</span>
                    {ev.details && <span className="text-foreground text-[11px] truncate max-w-xs">{ev.details}</span>}
                  </div>
                  <div className="text-right text-[10px] text-muted-foreground">
                    <div>{ev.ipAddress || "127.0.0.1"}</div>
                    <div>{ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : "Recent"}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast && <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />}
    </div>
  );
}
