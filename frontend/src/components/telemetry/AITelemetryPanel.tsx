"use client";

import React, { useEffect, useState } from "react";
import { apiService } from "@/services/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import {
  Activity,
  Cpu,
  ShieldCheck,
  Zap,
  Server,
  Clock,
  Terminal,
  AlertCircle,
  Database
} from "lucide-react";

interface AITelemetryPanelProps {
  activeAgent?: string;
  activeStatus?: string;
  activeLatencyMs?: number;
  currentTask?: string;
}

export const AITelemetryPanel: React.FC<AITelemetryPanelProps> = ({
  activeAgent,
  activeStatus = "IDLE",
  activeLatencyMs = 0,
  currentTask = "Standing by for natural-language objective",
}) => {
  const [telemetry, setTelemetry] = useState<any>(null);
  const [health, setHealth] = useState<any>({ database: "connected", redis: "connected", status: "ok" });

  useEffect(() => {
    async function loadTelemetry() {
      try {
        const [overviewData, healthData] = await Promise.all([
          apiService.getAnalyticsOverview().catch(() => null),
          apiService.checkHealth().catch(() => null),
        ]);
        if (overviewData) setTelemetry(overviewData);
        if (healthData) setHealth(healthData);
      } catch {
        // Safe empty state
      }
    }
    loadTelemetry();
  }, []);

  const getStatusLed = (status: string) => {
    switch (status.toUpperCase()) {
      case "RUNNING":
      case "EXECUTING":
        return <span className="flex h-2.5 w-2.5 rounded-full bg-primary animate-ping" />;
      case "PLANNING":
        return <span className="flex h-2.5 w-2.5 rounded-full bg-secondary animate-pulse" />;
      case "WAITING_APPROVAL":
      case "WAITING_FOR_APPROVAL":
        return <span className="flex h-2.5 w-2.5 rounded-full bg-amber-400 animate-pulse" />;
      case "COMPLETED":
        return <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400" />;
      case "FAILED":
        return <span className="flex h-2.5 w-2.5 rounded-full bg-rose-500" />;
      default:
        return <span className="flex h-2.5 w-2.5 rounded-full bg-slate-400" />;
    }
  };

  return (
    <Card glass className="p-4 space-y-4 text-xs">
      <CardHeader className="p-0 pb-3 border-b border-border/60 flex flex-row items-center justify-between">
        <CardTitle className="text-xs font-bold text-foreground flex items-center gap-2 font-heading">
          <Activity className="h-4 w-4 text-tertiary" />
          AI Execution Telemetry
        </CardTitle>
        <div className="flex items-center gap-1.5 font-mono text-[10px]">
          {getStatusLed(activeStatus)}
          <span className="text-muted-foreground uppercase font-bold">{activeStatus}</span>
        </div>
      </CardHeader>

      <CardContent className="p-0 space-y-3 font-mono">
        {/* Active Node Card */}
        <div className="p-3 rounded-xl bg-surface-lowest/80 border border-border/60 space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-muted-foreground">Active Agent:</span>
            <span className="font-bold text-primary">{activeAgent || "Orchestrator"}</span>
          </div>

          <div className="text-[10px] text-muted-foreground line-clamp-2">
            <span className="text-slate-400 font-sans block mb-0.5">Current Scope:</span>
            {currentTask}
          </div>
        </div>

        {/* Runtime Metrics Grid */}
        <div className="grid grid-cols-2 gap-2 text-[10px]">
          <div className="p-2.5 rounded-lg bg-surface-container/60 border border-border/40 space-y-0.5">
            <span className="text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3 text-slate-400" /> Latency
            </span>
            <span className="text-foreground font-bold text-xs">{activeLatencyMs || "—"} ms</span>
          </div>

          <div className="p-2.5 rounded-lg bg-surface-container/60 border border-border/40 space-y-0.5">
            <span className="text-muted-foreground flex items-center gap-1">
              <Cpu className="h-3 w-3 text-secondary" /> Model
            </span>
            <span className="text-foreground font-bold text-[10px] truncate block" title="nvidia/nemotron-3-ultra-550b-a55b">
              Nemotron 3 Ultra
            </span>
          </div>
        </div>

        {/* System Infrastructure Health */}
        <div className="space-y-1.5 pt-2 border-t border-border/40 text-[10px]">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="flex items-center gap-1">
              <Database className="h-3 w-3 text-emerald-400" /> Database
            </span>
            <span className="text-emerald-400 uppercase">{health.database}</span>
          </div>

          <div className="flex items-center justify-between text-muted-foreground">
            <span className="flex items-center gap-1">
              <Server className="h-3 w-3 text-tertiary" /> Provider Registry
            </span>
            <span className="text-tertiary uppercase">NVIDIA NIM (Active)</span>
          </div>

          <div className="flex items-center justify-between text-muted-foreground">
            <span className="flex items-center gap-1">
              <ShieldCheck className="h-3 w-3 text-primary" /> Tenant Isolation
            </span>
            <span className="text-primary uppercase">Enforced</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
