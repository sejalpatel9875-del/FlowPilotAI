"use client";

import React, { useEffect, useState } from "react";
import { WelcomeHeader } from "@/components/dashboard/WelcomeHeader";
import { AICommandCenter } from "@/components/command-center/AICommandCenter";
import { MetricCard } from "@/components/ui/MetricCard";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ActivityFeed } from "@/components/ui/ActivityFeed";
import { AITelemetryPanel } from "@/components/telemetry/AITelemetryPanel";
import { Lead, Project, AgentActivityEvent, Workflow } from "@/types";
import { apiService } from "@/services/api";
import {
  Users,
  Briefcase,
  Clock,
  GraduationCap,
  Sparkles,
  TrendingUp,
  Target,
  CheckCircle2,
  Calendar,
  AlertCircle,
  Cpu,
  BookOpen,
  Layers,
  Bot
} from "lucide-react";

export default function DashboardPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activities, setActivities] = useState<AgentActivityEvent[]>([]);
  const [activeWorkflow, setActiveWorkflow] = useState<Workflow | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      setIsLoading(true);
      try {
        const [leadsData, projectsData] = await Promise.all([
          apiService.getLeads().catch(() => []),
          apiService.getProjects().catch(() => []),
        ]);
        setLeads(leadsData);
        setProjects(projectsData);
      } catch (err) {
        console.error("Dashboard initialization error:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  const handleApproveAgent = async (id: string) => {
    try {
      await apiService.approveWorkflowAction(id, id);
    } catch (err) {
      console.error("Agent approval error:", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Welcome Section Header */}
      <WelcomeHeader />

      {/* 2. Central Cinematic AI Command Center & Multi-Agent Orchestrator */}
      <AICommandCenter onWorkflowStateChange={(wf) => setActiveWorkflow(wf)} />

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Leads"
          value={leads.length}
          changePercent={0}
          changePeriod="Real pipeline data"
          icon={<Users className="h-4 w-4 text-emerald-400" />}
        />
        <MetricCard
          title="Projects in Flight"
          value={projects.length}
          changePercent={0}
          changePeriod="Active engagements"
          icon={<Briefcase className="h-4 w-4 text-primary" />}
        />
        <MetricCard
          title="Specialized Agents"
          value="12"
          subtitle="All verified & active"
          icon={<Bot className="h-4 w-4 text-secondary" />}
        />
        <MetricCard
          title="LLM Gateway"
          value="Nemotron 3"
          subtitle="NVIDIA NIM Active"
          icon={<Cpu className="h-4 w-4 text-tertiary" />}
        />
      </div>

      {/* Grid Layout: Main Focus & Pipeline + Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Priorities, Pipeline, Projects */}
        <div className="lg:col-span-2 space-y-6">
          {/* Lead Pipeline Overview */}
          <Card glass hoverEffect={false}>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2 font-heading">
                  <Users className="h-4 w-4 text-emerald-400" />
                  Lead Pipeline
                </CardTitle>
                <CardDescription>Prospects, qualified leads, and outreach pipeline</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              {leads.length === 0 ? (
                <EmptyState
                  title="Lead Pipeline Empty"
                  description="No lead records exist in your PostgreSQL database yet. Add leads via the Leads module or import CSVs."
                  icon={<Users className="h-6 w-6 stroke-[1.5]" />}
                />
              ) : (
                <div className="space-y-2">
                  {leads.map((l) => (
                    <div key={l.id} className="p-3 rounded-lg bg-surface-container/60 border border-border/50 flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-foreground text-xs">{l.name}</span>
                        <span className="text-[11px] text-muted-foreground block">{l.company}</span>
                      </div>
                      <span className="px-2 py-0.5 text-[10px] rounded-full bg-emerald-500/20 text-emerald-300 font-mono">
                        ${l.value || 0}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Active Projects */}
          <Card glass hoverEffect={false}>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2 font-heading">
                  <Briefcase className="h-4 w-4 text-primary" />
                  Active Projects
                </CardTitle>
                <CardDescription>Client deliverables, milestone progress, and deadlines</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              {projects.length === 0 ? (
                <EmptyState
                  title="No Active Projects"
                  description="No client projects are currently registered in the database."
                  icon={<Briefcase className="h-6 w-6 stroke-[1.5]" />}
                />
              ) : (
                <div className="space-y-2">
                  {projects.map((p) => (
                    <div key={p.id} className="p-3 rounded-lg bg-surface-container/60 border border-border/50 flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-foreground text-xs">{p.title}</span>
                        <span className="text-[11px] text-muted-foreground block">{p.clientName}</span>
                      </div>
                      <span className="text-xs font-mono text-primary">{p.progressPercent}%</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column (1 Col): AI Telemetry & Observability */}
        <div className="space-y-6">
          <AITelemetryPanel
            activeAgent={activeWorkflow?.steps?.find((s) => s.status === "RUNNING")?.agent}
            activeStatus={activeWorkflow?.status || "IDLE"}
            activeLatencyMs={activeWorkflow?.steps?.reduce((acc, s) => acc + (s.latencyMs || 0), 0) || 0}
            currentTask={activeWorkflow?.goal || "Standing by for natural-language objective"}
          />

          {/* Scheduled Follow-ups */}
          <Card glass hoverEffect={false}>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2 font-heading">
                <Calendar className="h-4 w-4 text-rose-400" />
                Pending Follow-ups
              </CardTitle>
              <CardDescription>Scheduled client touchpoints & outreach reminders</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="No Follow-ups Pending"
                description="Zero upcoming client reminders queued."
                icon={<Calendar className="h-6 w-6 stroke-[1.5]" />}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
