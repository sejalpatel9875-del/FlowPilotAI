"use client";

import React, { useEffect, useState } from "react";
import { SystemStatusBar } from "@/components/mission-control/SystemStatusBar";
import { AgentConstellationGraph, AgentNodeData, FLEET_AGENTS } from "@/components/mission-control/AgentConstellationGraph";
import { AgentInspectorDrawer } from "@/components/mission-control/AgentInspectorDrawer";
import { LiveDecisionGate } from "@/components/mission-control/LiveDecisionGate";
import { AICommandCenter } from "@/components/command-center/AICommandCenter";
import { MetricCard } from "@/components/ui/MetricCard";
import { ActivityFeed } from "@/components/ui/ActivityFeed";
import { AITelemetryPanel } from "@/components/telemetry/AITelemetryPanel";
import { Lead, Project, AgentActivityEvent, Workflow } from "@/types";
import { apiService } from "@/services/api";
import {
  Users,
  Briefcase,
  Bot,
  Cpu,
  Zap,
  Activity,
  Layers,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";

export default function DashboardPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activities, setActivities] = useState<AgentActivityEvent[]>([
    {
      id: "act-1",
      agentName: "LeadAgent",
      action: "Scored inbound lead from Apex Dynamics",
      timestamp: "2 mins ago",
      status: "completed",
    },
    {
      id: "act-2",
      agentName: "ResearchAgent",
      action: "Enriched enterprise tech stack profile",
      timestamp: "6 mins ago",
      status: "completed",
    },
    {
      id: "act-3",
      agentName: "OutreachAgent",
      action: "Waiting for human authorization on email dispatch",
      timestamp: "12 mins ago",
      status: "needs_approval",
    },
  ]);
  const [selectedAgent, setSelectedAgent] = useState<AgentNodeData | null>(null);
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
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

  const handleSelectAgent = (agent: AgentNodeData) => {
    setSelectedAgent(agent);
    setIsInspectorOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* 1. Mission Control System Status Strip */}
      <SystemStatusBar
        activeAgentsCount={12}
        runningWorkflowsCount={3}
        pendingApprovalsCount={1}
        systemHealth={99.4}
      />

      {/* 2. Top Metric Strips */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Lead Intelligence Pipeline"
          value={leads.length || "14 Qualified"}
          changePercent={18.4}
          changePeriod="Real-time pipeline score"
          icon={<Users className="h-4 w-4 text-emerald-400" />}
        />
        <MetricCard
          title="Active Autonomous Projects"
          value={projects.length || "3 in Flight"}
          changePercent={12.5}
          changePeriod="Milestones progressing"
          icon={<Briefcase className="h-4 w-4 text-primary" />}
        />
        <MetricCard
          title="Specialized Agent Fleet"
          value="12 / 12"
          subtitle="All verified & active"
          icon={<Bot className="h-4 w-4 text-secondary" />}
        />
        <MetricCard
          title="NVIDIA NIM Gateway"
          value="Nemotron 3"
          subtitle="1,420 tokens / sec throughput"
          icon={<Cpu className="h-4 w-4 text-sky-400" />}
        />
      </div>

      {/* 3. Hero Command Center & Fleet Constellation Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <div className="xl:col-span-6 space-y-5">
          <AICommandCenter />
        </div>

        <div className="xl:col-span-6 space-y-5">
          <AgentConstellationGraph
            selectedAgentName={selectedAgent?.name}
            onSelectAgent={handleSelectAgent}
          />
        </div>
      </div>

      {/* 4. Human Decision Gate Area */}
      <LiveDecisionGate />

      {/* 5. Telemetry & Activity Feed Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <AITelemetryPanel />
        </div>
        <div className="lg:col-span-6">
          <ActivityFeed activities={activities} />
        </div>
      </div>

      {/* 6. Slide-out Agent Inspector */}
      <AgentInspectorDrawer
        agent={selectedAgent}
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
      />
    </div>
  );
}
