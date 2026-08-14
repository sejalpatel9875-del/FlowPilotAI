"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Tabs } from "@/components/ui/Tabs";
import {
  Layers,
  Wrench,
  Shield,
  Play,
  CheckCircle2,
  AlertTriangle,
  Activity,
  Cpu,
  Clock,
  Terminal,
  Server,
  Zap,
  Lock,
  FileCode,
  ShieldAlert,
  ArrowRight
} from "lucide-react";

interface MCPServerItem {
  id: string;
  name: string;
  description: string;
  status: string;
  version: string;
  tools_count: number;
}

interface MCPToolItem {
  name: string;
  description: string;
  serverName: string;
  riskLevel: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  requiredPermissions: string[];
  inputSchema: any;
  enabled: boolean;
}

interface AuditLogItem {
  executionId: string;
  action: string;
  ipAddress: string;
  details: string;
  timestamp: string;
}

export default function IntegrationsPage() {
  const [activeTab, setActiveTab] = useState("tools");
  const [servers, setServers] = useState<MCPServerItem[]>([]);
  const [tools, setTools] = useState<MCPToolItem[]>([]);
  const [executions, setExecutions] = useState<AuditLogItem[]>([]);

  const [selectedTool, setSelectedTool] = useState<MCPToolItem | null>(null);
  const [isTestModalOpen, setIsTestModalOpen] = useState(false);
  const [testInputJson, setTestInputJson] = useState("{}");
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchMCPData();
  }, []);

  const fetchMCPData = async () => {
    try {
      const [srvRes, toolRes, execRes] = await Promise.all([
        fetch("http://localhost:8000/api/v1/mcp/servers", { credentials: "include" }),
        fetch("http://localhost:8000/api/v1/mcp/tools", { credentials: "include" }),
        fetch("http://localhost:8000/api/v1/mcp/executions", { credentials: "include" }),
      ]);

      if (srvRes.ok) setServers((await srvRes.json()).servers || []);
      if (toolRes.ok) setTools((await toolRes.json()).tools || []);
      if (execRes.ok) setExecutions((await execRes.json()).executions || []);
    } catch (err) {
      console.error("Failed to load MCP data", err);
    }
  };

  const handleToggleTool = async (toolName: string, currentEnabled: boolean) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/mcp/tools/${toolName}/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ enabled: !currentEnabled }),
      });

      if (res.ok) {
        setToast({ type: "success", title: "Tool Toggled", message: `Tool '${toolName}' is now ${!currentEnabled ? 'enabled' : 'disabled'}.` });
        fetchMCPData();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to toggle tool state." });
    }
  };

  const handleOpenTestModal = (tool: MCPToolItem) => {
    setSelectedTool(tool);
    setTestInputJson(JSON.stringify(tool.inputSchema.properties || {}, null, 2));
    setTestResult(null);
    setIsTestModalOpen(true);
  };

  const handleRunToolTest = async () => {
    if (!selectedTool) return;
    setIsTesting(true);
    setTestResult(null);

    let parsedArgs = {};
    try {
      parsedArgs = JSON.parse(testInputJson);
    } catch (e) {
      setToast({ type: "error", title: "JSON Syntax Error", message: "Invalid input parameters format." });
      setIsTesting(false);
      return;
    }

    try {
      const res = await fetch(`http://localhost:8000/api/v1/mcp/tools/${selectedTool.name}/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          inputArgs: parsedArgs,
          agentName: "MCPTestConsole",
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Tool test error.");
      }

      const data = await res.json();
      setTestResult(data);
      fetchMCPData();
    } catch (err: any) {
      setToast({ type: "error", title: "Test Failed", message: err.message });
    } finally {
      setIsTesting(false);
    }
  };

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case "LOW": return <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono font-bold text-[10px]">LOW RISK</span>;
      case "MEDIUM": return <span className="px-2 py-0.5 rounded-md bg-sky-500/20 text-sky-300 border border-sky-500/30 font-mono font-bold text-[10px]">MEDIUM RISK</span>;
      case "HIGH": return <span className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono font-bold text-[10px]">HIGH RISK (APPROVAL REQ)</span>;
      case "CRITICAL": return <span className="px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono font-bold text-[10px]">CRITICAL (ADMIN REQ)</span>;
      default: return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Layers className="h-6 w-6 text-slate-400" />
            MCP Integrations & Tool Architecture
          </h1>
          <p className="text-xs text-muted-foreground">
            Model Context Protocol (MCP) tool registry, 4-tier Risk Level gatekeeping, and audit execution logs.
          </p>
        </div>

        <Badge variant="completed" className="font-mono text-xs">
          <Shield className="h-3 w-3 mr-1 text-emerald-400" />
          MCP Gateway Active
        </Badge>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Connected MCP Servers */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {servers.map((srv) => (
          <Card key={srv.id} glass className="p-4 flex flex-col justify-between space-y-3">
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <Server className="h-5 w-5 text-indigo-400" />
                <span className="text-[10px] font-mono text-emerald-400 font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                  {srv.status.toUpperCase()}
                </span>
              </div>
              <h4 className="text-sm font-bold text-foreground pt-1">{srv.name}</h4>
              <p className="text-[11px] text-muted-foreground line-clamp-2">{srv.description}</p>
            </div>
            <div className="pt-2 border-t border-border/50 text-[10px] font-mono text-muted-foreground flex justify-between">
              <span>v{srv.version}</span>
              <span>{srv.tools_count} Tools Registered</span>
            </div>
          </Card>
        ))}
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: "tools", label: `Registered MCP Tools (${tools.length})`, icon: <Wrench className="h-4 w-4" /> },
          { id: "audit", label: `Execution Audit Trail (${executions.length})`, icon: <Activity className="h-4 w-4 text-purple-400" /> },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {/* TAB 1: REGISTERED MCP TOOLS CATALOG */}
      {activeTab === "tools" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {tools.map((t) => (
            <Card key={t.name} glass className="p-5 flex flex-col justify-between space-y-4 hover:border-indigo-500/40 transition-all">
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-foreground font-mono">{t.name}</h3>
                      {getRiskBadge(t.riskLevel)}
                    </div>
                    <span className="text-[10px] text-muted-foreground font-mono block">{t.serverName}</span>
                  </div>

                  {/* Enable / Disable Switch */}
                  <label className="flex items-center gap-2 cursor-pointer">
                    <span className="text-[10px] font-mono text-muted-foreground">{t.enabled ? "Active" : "Disabled"}</span>
                    <input
                      type="checkbox"
                      checked={t.enabled}
                      onChange={() => handleToggleTool(t.name, t.enabled)}
                      className="rounded border-border accent-primary h-4 w-4"
                    />
                  </label>
                </div>

                <p className="text-xs text-muted-foreground">{t.description}</p>

                {/* Input Schema Parameters */}
                <div className="p-3 rounded-xl bg-card/60 border border-border/50 text-[11px] font-mono space-y-1">
                  <span className="text-muted-foreground block text-[10px]">JSON Schema Input Parameters:</span>
                  <span className="text-indigo-300 block">
                    {Object.keys(t.inputSchema.properties || {}).length > 0
                      ? Object.keys(t.inputSchema.properties).join(", ")
                      : "No parameters required"}
                  </span>
                </div>
              </div>

              <div className="pt-3 border-t border-border/50 flex items-center justify-between">
                <div className="flex items-center gap-2 text-[10px] font-mono text-muted-foreground">
                  <Lock className="h-3 w-3 text-slate-400" />
                  <span>Required: {t.requiredPermissions.join(", ")}</span>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleOpenTestModal(t)}
                  leftIcon={<Play className="h-3 w-3 text-purple-400" />}
                >
                  Test Execution
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* TAB 2: AUDIT LOG TRAIL */}
      {activeTab === "audit" && (
        <Card glass>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Activity className="h-4 w-4 text-purple-400" />
              Tool Execution Audit Logs
            </CardTitle>
            <CardDescription>Auditable record of all MCP tool invocations with IP signatures and status</CardDescription>
          </CardHeader>

          <CardContent>
            {executions.length === 0 ? (
              <div className="p-6 text-center text-xs text-muted-foreground">
                No tool executions logged yet. Use the "Test Execution" button on any tool to generate audit entries.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="border-b border-border/60 text-muted-foreground bg-muted/20">
                    <tr>
                      <th className="py-3 px-4 font-semibold">Execution ID</th>
                      <th className="py-3 px-4 font-semibold">Tool Name</th>
                      <th className="py-3 px-4 font-semibold">IP Address</th>
                      <th className="py-3 px-4 font-semibold">Execution Details</th>
                      <th className="py-3 px-4 font-semibold">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {executions.map((log) => (
                      <tr key={log.executionId} className="hover:bg-muted/30">
                        <td className="py-3 px-4 text-indigo-400 font-bold">{log.executionId}</td>
                        <td className="py-3 px-4 font-bold text-foreground">{log.action}</td>
                        <td className="py-3 px-4 text-muted-foreground">{log.ipAddress}</td>
                        <td className="py-3 px-4 text-slate-300 max-w-xs truncate">{log.details}</td>
                        <td className="py-3 px-4 text-muted-foreground">{log.timestamp}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* TEST TOOL MODAL */}
      {selectedTool && (
        <Modal
          isOpen={isTestModalOpen}
          onClose={() => setIsTestModalOpen(false)}
          title={`Test MCP Tool '${selectedTool.name}'`}
        >
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-secondary/30 border border-border/60 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-foreground font-mono">{selectedTool.name}</span>
                {getRiskBadge(selectedTool.riskLevel)}
              </div>
              <p className="text-[11px] text-muted-foreground">{selectedTool.description}</p>
            </div>

            <div className="space-y-1">
              <label className="font-semibold text-foreground">Input JSON Parameters</label>
              <textarea
                rows={4}
                value={testInputJson}
                onChange={(e) => setTestInputJson(e.target.value)}
                className="w-full rounded-xl glass-panel bg-secondary/40 p-3 text-xs text-slate-200 font-mono focus:outline-none focus:ring-2 focus:ring-primary border-border/80 resize-none"
              />
            </div>

            {testResult && (
              <div className="p-3.5 rounded-xl glass-panel bg-secondary/50 border border-purple-500/30 space-y-2 font-mono text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-purple-300 font-bold">Execution Result</span>
                  <Badge variant={testResult.requiresApproval ? "failed" : "completed"}>
                    {testResult.status}
                  </Badge>
                </div>

                {testResult.resultData && (
                  <pre className="text-slate-200 text-[11px] bg-card/60 p-2.5 rounded-lg overflow-x-auto">
                    {JSON.stringify(testResult.resultData, null, 2)}
                  </pre>
                )}

                {testResult.requiresApproval && (
                  <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-[10px] space-y-1">
                    <span className="font-bold block">Approval Gate triggered for [{testResult.riskLevel}] risk level!</span>
                    <p>{testResult.actionToApprove}</p>
                  </div>
                )}
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setIsTestModalOpen(false)}>
                Close
              </Button>
              <Button variant="primary" size="sm" onClick={handleRunToolTest} isLoading={isTesting}>
                Dispatch Test Call
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
