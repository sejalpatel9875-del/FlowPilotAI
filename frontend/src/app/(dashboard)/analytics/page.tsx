"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Tabs } from "@/components/ui/Tabs";
import {
  BarChart3,
  TrendingUp,
  Users,
  Target,
  Mail,
  Calendar,
  FileText,
  Award,
  DollarSign,
  BookOpen,
  Clock,
  Cpu,
  Zap,
  ShieldCheck,
  CheckCircle2,
  Activity,
  Layers
} from "lucide-react";

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<any>(null);
  const [charts, setCharts] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      const [overviewRes, chartsRes] = await Promise.all([
        fetch("http://localhost:8000/api/v1/analytics/overview", { credentials: "include" }),
        fetch("http://localhost:8000/api/v1/analytics/charts", { credentials: "include" }),
      ]);

      if (overviewRes.ok && chartsRes.ok) {
        setOverview(await overviewRes.json());
        setCharts(await chartsRes.json());
      }
    } catch (err) {
      console.error("Failed to load analytics data", err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || !overview) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-muted-foreground font-mono text-xs">
        Loading Real Database Analytics...
      </div>
    );
  }

  const cards = overview.summaryCards;
  const dims = overview.trackedDimensions;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-primary" />
            FlowPilot Analytics System
          </h1>
          <p className="text-xs text-muted-foreground">
            100% Real Database Analytics computed live across 11 domain dimensions.
          </p>
        </div>

        <Badge variant="completed">
          REAL DATABASE DATA
        </Badge>
      </div>

      {/* 9 DASHBOARD SUMMARY CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <Card glass className="p-3.5 space-y-1 hover:border-primary/40 transition-all">
          <span className="text-[11px] text-muted-foreground font-mono flex items-center gap-1.5">
            <Users className="h-3.5 w-3.5 text-primary" /> Leads
          </span>
          <span className="text-xl font-bold text-foreground font-mono">{cards.leads}</span>
        </Card>

        <Card glass className="p-3.5 space-y-1 hover:border-primary/40 transition-all">
          <span className="text-[11px] text-muted-foreground font-mono flex items-center gap-1.5">
            <Target className="h-3.5 w-3.5 text-amber-400" /> Qualified Leads
          </span>
          <span className="text-xl font-bold text-foreground font-mono">{cards.qualifiedLeads}</span>
        </Card>

        <Card glass className="p-3.5 space-y-1 hover:border-primary/40 transition-all">
          <span className="text-[11px] text-muted-foreground font-mono flex items-center gap-1.5">
            <Mail className="h-3.5 w-3.5 text-sky-400" /> Response Rate
          </span>
          <span className="text-xl font-bold text-foreground font-mono">{cards.responseRate}%</span>
        </Card>

        <Card glass className="p-3.5 space-y-1 hover:border-primary/40 transition-all">
          <span className="text-[11px] text-muted-foreground font-mono flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5 text-purple-400" /> Meetings
          </span>
          <span className="text-xl font-bold text-foreground font-mono">{cards.meetings}</span>
        </Card>

        <Card glass className="p-3.5 space-y-1 hover:border-primary/40 transition-all">
          <span className="text-[11px] text-muted-foreground font-mono flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5 text-indigo-400" /> Proposals
          </span>
          <span className="text-xl font-bold text-foreground font-mono">{cards.proposals}</span>
        </Card>

        <Card glass className="p-3.5 space-y-1 hover:border-primary/40 transition-all">
          <span className="text-[11px] text-muted-foreground font-mono flex items-center gap-1.5">
            <Award className="h-3.5 w-3.5 text-emerald-400" /> Won Clients
          </span>
          <span className="text-xl font-bold text-foreground font-mono">{cards.wonClients}</span>
        </Card>

        <Card glass className="p-3.5 space-y-1 hover:border-primary/40 transition-all">
          <span className="text-[11px] text-muted-foreground font-mono flex items-center gap-1.5">
            <DollarSign className="h-3.5 w-3.5 text-emerald-400" /> Pipeline
          </span>
          <span className="text-xl font-bold text-foreground font-mono">${cards.pipelineValue.toLocaleString()}</span>
        </Card>

        <Card glass className="p-3.5 space-y-1 hover:border-primary/40 transition-all">
          <span className="text-[11px] text-muted-foreground font-mono flex items-center gap-1.5">
            <BookOpen className="h-3.5 w-3.5 text-amber-400" /> Learning Hours
          </span>
          <span className="text-xl font-bold text-foreground font-mono">{cards.learningHours} hrs</span>
        </Card>

        <Card glass className="p-3.5 space-y-1 hover:border-primary/40 transition-all col-span-2 sm:col-span-1">
          <span className="text-[11px] text-muted-foreground font-mono flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-sky-400" /> Focus Hours
          </span>
          <span className="text-xl font-bold text-foreground font-mono">{cards.focusHours} hrs</span>
        </Card>
      </div>

      {/* 5 CHARTS GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Chart 1: Lead Funnel */}
        <Card glass className="p-5 space-y-3 border-border/60">
          <h3 className="text-xs font-bold text-foreground font-mono flex items-center gap-2">
            <Target className="h-4 w-4 text-amber-400" /> 1. Lead Conversion Funnel
          </h3>
          <div className="space-y-2 font-mono text-xs">
            {charts?.leadFunnel.map((item: any, idx: number) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-muted-foreground">{item.stage}</span>
                  <span className="font-bold text-foreground">{item.count}</span>
                </div>
                <div className="w-full bg-secondary/50 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-amber-400 h-full rounded-full transition-all"
                    style={{ width: `${Math.min((item.count / max(cards.leads, 1)) * 100, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Chart 2: Weekly Productivity */}
        <Card glass className="p-5 space-y-3 border-border/60">
          <h3 className="text-xs font-bold text-foreground font-mono flex items-center gap-2">
            <Clock className="h-4 w-4 text-sky-400" /> 2. Weekly Focus Productivity
          </h3>
          <div className="grid grid-cols-7 gap-2 text-center font-mono text-xs pt-2">
            {charts?.weeklyProductivity.map((item: any, idx: number) => (
              <div key={idx} className="space-y-1">
                <div className="h-24 bg-secondary/40 rounded-lg flex items-end justify-center p-1">
                  <div
                    className="w-full bg-sky-400/80 rounded-md transition-all"
                    style={{ height: `${Math.min((item.focusHours / 8.0) * 100, 100)}%` }}
                  />
                </div>
                <span className="text-[10px] text-muted-foreground block">{item.day}</span>
                <span className="text-[10px] font-bold text-foreground block">{item.focusHours}h</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Chart 3: Learning Progress */}
        <Card glass className="p-5 space-y-3 border-border/60">
          <h3 className="text-xs font-bold text-foreground font-mono flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-purple-400" /> 3. Skill Learning Progress
          </h3>
          <div className="space-y-3 font-mono text-xs">
            {charts?.learningProgress.map((item: any, idx: number) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-foreground font-bold">{item.skill}</span>
                  <span className="text-muted-foreground">{item.loggedHours} / {item.targetHours} hrs</span>
                </div>
                <div className="w-full bg-secondary/50 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-purple-400 h-full rounded-full transition-all"
                    style={{ width: `${Math.min((item.loggedHours / item.targetHours) * 100, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Chart 4: Agent Activity */}
        <Card glass className="p-5 space-y-3 border-border/60">
          <h3 className="text-xs font-bold text-foreground font-mono flex items-center gap-2">
            <Cpu className="h-4 w-4 text-indigo-400" /> 4. AI Agent Activity
          </h3>
          <div className="space-y-2 font-mono text-xs">
            {charts?.agentActivity.map((item: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-card/60 border border-border/40">
                <span className="text-foreground font-bold">{item.agent}</span>
                <Badge variant="purple">{item.runs} Executions</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* 11 TRACKED METRIC DIMENSIONS BREAKDOWN TABLE */}
      <Card glass className="p-5 space-y-4 border-border/60">
        <h3 className="text-sm font-bold text-foreground font-mono flex items-center gap-2">
          <Activity className="h-4 w-4 text-emerald-400" />
          11 Tracked Performance Dimensions (Live DB Query)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-xs">
          <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
            <span className="text-muted-foreground text-[10px]">1. Lead Conversion</span>
            <div className="flex justify-between font-bold text-foreground">
              <span>Leads: {dims.leadConversion.total}</span>
              <span className="text-emerald-400">Won: {dims.leadConversion.won}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
            <span className="text-muted-foreground text-[10px]">2. Outreach Performance</span>
            <div className="flex justify-between font-bold text-foreground">
              <span>Sent: {dims.outreachPerformance.sent}</span>
              <span className="text-sky-400">Resp: {dims.outreachPerformance.responseRate}%</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
            <span className="text-muted-foreground text-[10px]">3. Follow-up Cadence</span>
            <div className="flex justify-between font-bold text-foreground">
              <span>Active: {dims.followupPerformance.activeSequences}</span>
              <span className="text-purple-400">Done: {dims.followupPerformance.completed}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
            <span className="text-muted-foreground text-[10px]">4. Proposal Conversion</span>
            <div className="flex justify-between font-bold text-foreground">
              <span>Proposals: {dims.proposalConversion.proposals}</span>
              <span className="text-emerald-400">Rate: {dims.proposalConversion.conversionRate}%</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
            <span className="text-muted-foreground text-[10px]">5. Client Acquisition</span>
            <div className="flex justify-between font-bold text-foreground">
              <span>Clients: {dims.clientAcquisition.wonClients}</span>
              <span className="text-emerald-400">${dims.clientAcquisition.pipelineValue.toLocaleString()}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
            <span className="text-muted-foreground text-[10px]">6. Agent Performance</span>
            <div className="flex justify-between font-bold text-foreground">
              <span>Runs: {dims.agentPerformance.totalRuns}</span>
              <span className="text-purple-400">Success: {dims.agentPerformance.successRate}%</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

function max(a: number, b: number) {
  return a > b ? a : b;
}
