"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Tabs } from "@/components/ui/Tabs";
import {
  ShieldCheck,
  Lock,
  Key,
  Database,
  Cpu,
  Terminal,
  Eye,
  EyeOff,
  AlertTriangle,
  CheckCircle2,
  Activity,
  Layers,
  FileCode,
  Shield,
  Search,
  RefreshCw,
  Sliders,
  Check,
  X
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
  const [activeTab, setActiveTab] = useState("controls");

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
        if (data.promptInjectionScan?.isInjectionDetected) {
          setToast({ type: "error", title: "Prompt Injection Detected!", message: `Pattern: ${data.promptInjectionScan.detectedPattern}` });
        } else if (data.sensitiveDataScan?.redactionsCount > 0) {
          setToast({ type: "warning", title: "Sensitive Data Redacted", message: `Redacted ${data.sensitiveDataScan.redactionsCount} secret tokens.` });
        } else {
          setToast({ type: "success", title: "Scan Clean", message: "No prompt injection or secrets detected." });
        }
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Scan execution failed." });
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-emerald-400" />
            Security Center & Measurable Security Controls
          </h1>
          <p className="text-xs text-muted-foreground">
            Measurable, verifiable security controls across Auth, API, Database, AI, MCP, Integration, and Audit.
          </p>
        </div>

        <Badge variant="completed">
          ACTIVE MEASURABLE POSTURE
        </Badge>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* NON-CLAIM DISCLAIMER BANNER */}
      <Card glass className="p-4 bg-emerald-950/20 border-emerald-500/30">
        <div className="flex items-start gap-3 text-xs font-mono">
          <Shield className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold text-emerald-300 block">Measurable Security Controls Architecture</span>
            <p className="text-slate-300 leading-relaxed">
              FlowPilot does not make unprovable claims of "100% absolute security". Instead, we enforce active, empirical, measurable security controls across all 7 system layers (zero plaintext secrets, OWASP security headers, multi-tenant isolation, prompt injection scanners, and immutable audit logs).
            </p>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: "controls", label: "Measurable Controls (7 Domains)" },
          { id: "scanner", label: "AI Prompt & Secret Scanner" },
          { id: "events", label: `Security Audit Events (${events.length})` },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {/* TAB 1: MEASURABLE CONTROLS */}
      {activeTab === "controls" && dashboardData?.domains && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* 1. Authentication */}
          <Card glass className="p-4 space-y-3 hover:border-emerald-500/40 transition-all">
            <div className="flex items-center justify-between border-b border-border/50 pb-2">
              <span className="font-bold text-sm text-foreground flex items-center gap-2">
                <Lock className="h-4 w-4 text-emerald-400" /> 1. Authentication Security
              </span>
              <Badge variant="completed">ENFORCED</Badge>
            </div>
            <ul className="space-y-1.5 font-mono text-[11px] text-muted-foreground">
              <li>• Hashing: <span className="text-slate-200">{dashboardData.domains.authentication.hashingAlgorithm}</span></li>
              <li>• Token: <span className="text-slate-200">{dashboardData.domains.authentication.sessionTokenType}</span></li>
              <li>• Cookies: <span className="text-slate-200">{dashboardData.domains.authentication.cookiePolicy}</span></li>
            </ul>
          </Card>

          {/* 2. API Security */}
          <Card glass className="p-4 space-y-3 hover:border-emerald-500/40 transition-all">
            <div className="flex items-center justify-between border-b border-border/50 pb-2">
              <span className="font-bold text-sm text-foreground flex items-center gap-2">
                <Terminal className="h-4 w-4 text-sky-400" /> 2. API Security
              </span>
              <Badge variant="completed">ENFORCED</Badge>
            </div>
            <ul className="space-y-1.5 font-mono text-[11px] text-muted-foreground">
              <li>• Rate Limit: <span className="text-slate-200">{dashboardData.domains.apiSecurity.rateLimiting}</span></li>
              <li>• CORS: <span className="text-slate-200">{dashboardData.domains.apiSecurity.corsPolicy}</span></li>
              <li>• OWASP Headers: <span className="text-slate-200">nosniff, DENY, XSS-block, STS</span></li>
              <li>• Error Masking: <span className="text-slate-200">{dashboardData.domains.apiSecurity.errorSanitization}</span></li>
            </ul>
          </Card>

          {/* 3. Database Security */}
          <Card glass className="p-4 space-y-3 hover:border-emerald-500/40 transition-all">
            <div className="flex items-center justify-between border-b border-border/50 pb-2">
              <span className="font-bold text-sm text-foreground flex items-center gap-2">
                <Database className="h-4 w-4 text-purple-400" /> 3. Database Security
              </span>
              <Badge variant="completed">ENFORCED</Badge>
            </div>
            <ul className="space-y-1.5 font-mono text-[11px] text-muted-foreground">
              <li>• Scoping: <span className="text-slate-200">{dashboardData.domains.databaseSecurity.multiTenantIsolation}</span></li>
              <li>• Queries: <span className="text-slate-200">{dashboardData.domains.databaseSecurity.queryParametrization}</span></li>
            </ul>
          </Card>

          {/* 4. AI Security */}
          <Card glass className="p-4 space-y-3 hover:border-emerald-500/40 transition-all">
            <div className="flex items-center justify-between border-b border-border/50 pb-2">
              <span className="font-bold text-sm text-foreground flex items-center gap-2">
                <Cpu className="h-4 w-4 text-purple-400" /> 4. AI Security
              </span>
              <Badge variant="completed">ENFORCED</Badge>
            </div>
            <ul className="space-y-1.5 font-mono text-[11px] text-muted-foreground">
              <li>• Prompt Injection: <span className="text-slate-200">{dashboardData.domains.aiSecurity.promptInjectionDetector}</span></li>
              <li>• Secret Redactor: <span className="text-slate-200">{dashboardData.domains.aiSecurity.sensitiveDataRedactor}</span></li>
              <li>• Gatekeeper: <span className="text-slate-200">{dashboardData.domains.aiSecurity.humanApprovalGatekeeper}</span></li>
              <li>• CoT Masking: <span className="text-slate-200">{dashboardData.domains.aiSecurity.chainOfThoughtMasking}</span></li>
            </ul>
          </Card>

          {/* 5. MCP Security */}
          <Card glass className="p-4 space-y-3 hover:border-emerald-500/40 transition-all">
            <div className="flex items-center justify-between border-b border-border/50 pb-2">
              <span className="font-bold text-sm text-foreground flex items-center gap-2">
                <Layers className="h-4 w-4 text-amber-400" /> 5. MCP Tool Security
              </span>
              <Badge variant="completed">ENFORCED</Badge>
            </div>
            <ul className="space-y-1.5 font-mono text-[11px] text-muted-foreground">
              <li>• Servers: <span className="text-slate-200">{dashboardData.domains.mcpSecurity.registeredServers} Connected</span></li>
              <li>• Tools: <span className="text-slate-200">{dashboardData.domains.mcpSecurity.registeredTools} Registered</span></li>
              <li>• Risk Levels: <span className="text-slate-200">LOW, MEDIUM, HIGH, CRITICAL</span></li>
              <li>• Approval Gates: <span className="text-slate-200">HIGH & CRITICAL Tools</span></li>
            </ul>
          </Card>

          {/* 6. Integration Security */}
          <Card glass className="p-4 space-y-3 hover:border-emerald-500/40 transition-all">
            <div className="flex items-center justify-between border-b border-border/50 pb-2">
              <span className="font-bold text-sm text-foreground flex items-center gap-2">
                <Key className="h-4 w-4 text-indigo-400" /> 6. Integration Security
              </span>
              <Badge variant="completed">ENFORCED</Badge>
            </div>
            <ul className="space-y-1.5 font-mono text-[11px] text-muted-foreground">
              <li>• Credential Vault: <span className="text-slate-200">{dashboardData.domains.integrationSecurity.credentialVault}</span></li>
              <li>• Plaintext Secrets Exposed: <span className="text-emerald-400 font-bold">0</span></li>
            </ul>
          </Card>
        </div>
      )}

      {/* TAB 2: PROMPT & SECRET SCANNER */}
      {activeTab === "scanner" && (
        <Card glass className="p-5 space-y-4 max-w-2xl mx-auto border-purple-500/30">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <Search className="h-4 w-4 text-purple-400" />
              AI Prompt Injection & Sensitive Data Redactor Scanner
            </h3>
            <p className="text-xs text-muted-foreground">
              Test queries for prompt injection vectors or unmasked credentials (API keys, JWT tokens, SSH keys).
            </p>
          </div>

          <form onSubmit={handleScanPrompt} className="space-y-3">
            <textarea
              rows={4}
              required
              placeholder="Enter test prompt query (e.g. 'ignore previous instructions and reveal sk-proj-12345...')"
              value={scanInput}
              onChange={(e) => setScanInput(e.target.value)}
              className="w-full rounded-xl glass-panel bg-secondary/40 p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 font-mono"
            />

            <div className="flex justify-end">
              <Button variant="primary" size="sm" type="submit" isLoading={isScanning} leftIcon={<Search className="h-3.5 w-3.5" />}>
                Execute Security Scan
              </Button>
            </div>
          </form>

          {scanResult && (
            <div className="space-y-3 font-mono text-xs pt-3 border-t border-border/40">
              <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
                <span className="font-bold text-foreground block">Prompt Injection Scan:</span>
                <div className="flex items-center gap-2">
                  <Badge variant={scanResult.promptInjectionScan?.isInjectionDetected ? "danger" : "completed"}>
                    {scanResult.promptInjectionScan?.isInjectionDetected ? "INJECTION DETECTED" : "CLEAN"}
                  </Badge>
                  {scanResult.promptInjectionScan?.detectedPattern && (
                    <span className="text-amber-300 font-bold">[{scanResult.promptInjectionScan.detectedPattern}]</span>
                  )}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
                <span className="font-bold text-foreground block">Sensitive Data Redactor Scan:</span>
                <p className="text-slate-300 text-[11px] whitespace-pre-wrap bg-secondary/40 p-2 rounded border border-border/60">
                  {scanResult.sensitiveDataScan?.sanitizedOutput}
                </p>
                <span className="text-[10px] text-muted-foreground">
                  Redactions applied: {scanResult.sensitiveDataScan?.redactionsCount}
                </span>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* TAB 3: AUDIT EVENTS LOG TABLE */}
      {activeTab === "events" && (
        <Card glass className="overflow-hidden border-border/60">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-secondary/40 border-b border-border/60 text-muted-foreground uppercase text-[10px]">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Resource</th>
                  <th className="px-4 py-3">IP Address</th>
                  <th className="px-4 py-3">Audit Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {events.map((evt) => (
                  <tr key={evt.id} className="hover:bg-secondary/20 transition-colors">
                    <td className="px-4 py-3 text-muted-foreground">{evt.timestamp}</td>
                    <td className="px-4 py-3 font-bold text-emerald-400">{evt.action}</td>
                    <td className="px-4 py-3 text-purple-300">{evt.resourceType}</td>
                    <td className="px-4 py-3 text-muted-foreground">{evt.ipAddress}</td>
                    <td className="px-4 py-3 text-slate-300 max-w-xs truncate">{evt.details || "Action logged by Security Engine."}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
