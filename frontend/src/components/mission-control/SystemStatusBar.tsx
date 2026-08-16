"use client";

import React, { useState, useEffect } from "react";
import { Activity, Zap, Layers, ShieldCheck, CheckCircle2, Cpu, Clock, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

export interface SystemStatusBarProps {
  activeAgentsCount?: number;
  runningWorkflowsCount?: number;
  pendingApprovalsCount?: number;
  systemHealth?: number;
  className?: string;
}

export const SystemStatusBar: React.FC<SystemStatusBarProps> = ({
  activeAgentsCount = 12,
  runningWorkflowsCount = 3,
  pendingApprovalsCount = 1,
  systemHealth = 99.4,
  className = "",
}) => {
  const [currentTime, setCurrentTime] = useState<string>("");
  const [throughputTokens, setThroughputTokens] = useState<number>(1420);

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }) + " UTC");
    };
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const jitter = setInterval(() => {
      setThroughputTokens(1400 + Math.floor(Math.random() * 80));
    }, 3000);
    return () => clearInterval(jitter);
  }, []);

  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 px-4 py-2 rounded-xl glass-panel bg-surface-lowest/80 border border-border/70 text-xs font-mono select-none ${className}`}
    >
      {/* Left: System Operational Indicator */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="font-bold text-foreground tracking-wider uppercase text-[11px]">
            SYSTEM OPERATIONAL
          </span>
        </div>

        <div className="h-3 w-[1px] bg-border/80 hidden sm:block" />

        {/* 12 Agents Active */}
        <div className="flex items-center gap-1.5 text-muted-foreground">
          <Cpu className="h-3.5 w-3.5 text-primary" />
          <span className="text-foreground font-bold">{activeAgentsCount}</span>
          <span>AGENTS ACTIVE</span>
        </div>

        <div className="h-3 w-[1px] bg-border/80 hidden sm:block" />

        {/* Workflows Running */}
        <div className="flex items-center gap-1.5 text-muted-foreground">
          <Layers className="h-3.5 w-3.5 text-secondary" />
          <span className="text-foreground font-bold">{runningWorkflowsCount}</span>
          <span>WORKFLOWS RUNNING</span>
        </div>

        <div className="h-3 w-[1px] bg-border/80 hidden md:block" />

        {/* Human Approvals Gate */}
        {pendingApprovalsCount > 0 && (
          <div className="flex items-center gap-1.5 text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span className="font-bold">{pendingApprovalsCount}</span>
            <span>APPROVAL REQUIRED</span>
          </div>
        )}
      </div>

      {/* Right: Telemetry Health & Clock */}
      <div className="flex items-center gap-4 flex-wrap ml-auto">
        <div className="flex items-center gap-1.5 text-muted-foreground hidden lg:flex">
          <Zap className="h-3.5 w-3.5 text-sky-400" />
          <span>NIM:</span>
          <span className="text-foreground font-bold">{throughputTokens} tps</span>
        </div>

        <div className="flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5 text-emerald-400" />
          <span className="text-muted-foreground">HEALTH:</span>
          <span className="text-emerald-400 font-bold">{systemHealth}%</span>
        </div>

        <div className="flex items-center gap-1.5 text-muted-foreground hidden sm:flex">
          <Clock className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-foreground">{currentTime}</span>
        </div>
      </div>
    </div>
  );
};
