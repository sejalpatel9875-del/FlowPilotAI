"use client";

import React, { useEffect, useState } from "react";
import { WelcomeHeader } from "@/components/dashboard/WelcomeHeader";
import { AICommandCenter } from "@/components/command-center/AICommandCenter";
import { MetricCard } from "@/components/ui/MetricCard";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ActivityFeed } from "@/components/ui/ActivityFeed";
import { Lead, Project, AgentActivityEvent } from "@/types";
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
  BookOpen
} from "lucide-react";

export default function DashboardPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activities, setActivities] = useState<AgentActivityEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      setIsLoading(true);
      try {
        const [leadsData, projectsData, activitiesData] = await Promise.all([
          apiService.getLeads(),
          apiService.getProjects(),
          apiService.getAgentActivities(),
        ]);
        setLeads(leadsData);
        setProjects(projectsData);
        setActivities(activitiesData);
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
      await apiService.approveAgentAction(id);
      const updated = await apiService.getAgentActivities();
      setActivities(updated);
    } catch (err) {
      console.error("Agent approval error:", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Welcome Section Header */}
      <WelcomeHeader />

      {/* 2. Central AI Command Center */}
      <AICommandCenter />

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
          icon={<Briefcase className="h-4 w-4 text-sky-400" />}
        />
        <MetricCard
          title="Time Logged"
          value="0.0 hrs"
          subtitle="This week's utilization"
          icon={<Clock className="h-4 w-4 text-purple-400" />}
        />
        <MetricCard
          title="Learning Modules"
          value="0"
          subtitle="Courses in progress"
          icon={<GraduationCap className="h-4 w-4 text-amber-400" />}
        />
      </div>

      {/* Grid Layout: Main Focus & Pipeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Priorities, Pipeline, Projects */}
        <div className="lg:col-span-2 space-y-6">
          {/* Today's Priorities */}
          <Card glass hoverEffect={false}>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Target className="h-4 w-4 text-indigo-400" />
                  Today's Priorities
                </CardTitle>
                <CardDescription>Intelligent task queue prioritized by urgency and revenue impact</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="No Priority Tasks Scheduled"
                description="Your priority queue is clear. Use the AI Command Center above to generate task recommendations based on your leads and project deadlines."
                icon={<CheckCircle2 className="h-6 w-6 stroke-[1.5]" />}
              />
            </CardContent>
          </Card>

          {/* Lead Pipeline Overview */}
          <Card glass hoverEffect={false}>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
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
                    <div key={l.id} className="p-3 rounded-lg bg-card/60 border border-border/50 flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-foreground text-xs">{l.name}</span>
                        <span className="text-[11px] text-muted-foreground block">{l.company}</span>
                      </div>
                      <span className="px-2 py-0.5 text-[10px] rounded-full bg-emerald-500/20 text-emerald-300 font-mono">
                        ${l.value}
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
                <CardTitle className="text-base flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-sky-400" />
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
                    <div key={p.id} className="p-3 rounded-lg bg-card/60 border border-border/50 flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-foreground text-xs">{p.title}</span>
                        <span className="text-[11px] text-muted-foreground block">{p.clientName}</span>
                      </div>
                      <span className="text-xs font-mono text-indigo-400">{p.progressPercent}%</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column (1 Col): Agent Activity, Follow-ups, Learning */}
        <div className="space-y-6">
          {/* Agent Activity Component */}
          <Card glass hoverEffect={false}>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-purple-400" />
                  Agent Activity Stream
                </CardTitle>
                <CardDescription>Autonomous agent execution events & approvals</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <ActivityFeed
                activities={activities}
                isLoading={isLoading}
                onApprove={handleApproveAgent}
              />
            </CardContent>
          </Card>

          {/* Scheduled Follow-ups */}
          <Card glass hoverEffect={false}>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
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

          {/* Learning Progress */}
          <Card glass hoverEffect={false}>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-emerald-400" />
                Learning & Skill Progress
              </CardTitle>
              <CardDescription>Upskilling pathways and article reading lists</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="No Active Pathways"
                description="Skill tracks and course goals will display here."
                icon={<BookOpen className="h-6 w-6 stroke-[1.5]" />}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
