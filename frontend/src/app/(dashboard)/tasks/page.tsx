"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Tabs } from "@/components/ui/Tabs";
import {
  Calendar as CalendarIcon,
  Clock,
  Sparkles,
  CheckCircle2,
  XCircle,
  Play,
  Scissors,
  Minimize2,
  RefreshCw,
  Target,
  BookOpen,
  Coffee,
  Check,
  Zap,
  Maximize2,
  BarChart2,
  Sliders,
  Layers
} from "lucide-react";

interface TimeBlock {
  id: string;
  title: string;
  blockType: "FOCUS" | "LEARNING" | "BREAK" | "FIXED";
  startTime: string;
  endTime: string;
  status: "SCHEDULED" | "COMPLETED" | "SKIPPED" | "RESCHEDULED" | "REDUCED_SCOPE";
}

export default function TasksPage() {
  const [viewMode, setViewMode] = useState<"today" | "week" | "focus">("today");
  const [timeBlocks, setTimeBlocks] = useState<TimeBlock[]>([]);
  const [topPriorities, setTopPriorities] = useState<string[]>([
    "1. Deliver High-Revenue Client Feature Architecture",
    "2. Conduct Deep Research on Client Pain Points",
    "3. Dedicated AI Agent Skill Mastery Session"
  ]);

  // Quick Plan "I only have X minutes"
  const [quickMinutes, setQuickMinutes] = useState(60);
  const [isPlanning, setIsPlanning] = useState(false);
  const [quickPlanResult, setQuickPlanResult] = useState<string | null>(null);

  // Focus Mode State
  const [activeFocusBlock, setActiveFocusBlock] = useState<TimeBlock | null>(null);
  const [focusSecondsLeft, setFocusSecondsLeft] = useState(1500); // 25 min timer

  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchSchedule();
  }, [viewMode]);

  useEffect(() => {
    let timer: any;
    if (viewMode === "focus" && focusSecondsLeft > 0) {
      timer = setInterval(() => setFocusSecondsLeft((prev) => prev - 1), 1000);
    }
    return () => clearInterval(timer);
  }, [viewMode, focusSecondsLeft]);

  const fetchSchedule = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/time/schedule?view=${viewMode === 'week' ? 'week' : 'today'}`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setTimeBlocks(data.timeBlocks || []);
        if (data.topPriorities) setTopPriorities(data.topPriorities);
      }
    } catch (err) {
      console.error("Failed to load schedule", err);
    }
  };

  const handlePlanMyDay = async () => {
    setIsPlanning(true);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/time/plan-day", {
        method: "POST",
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Daily planner failed.");
      }

      const data = await res.json();
      setToast({ type: "success", title: "Day Planned by AI", message: `Scheduled ${data.totalBlocksScheduled} optimized time blocks.` });
      if (data.topPriorities) setTopPriorities(data.topPriorities);
      fetchSchedule();
    } catch (err: any) {
      setToast({ type: "error", title: "Planning Failed", message: err.message });
    } finally {
      setIsPlanning(false);
    }
  };

  const handleQuickPlan = async () => {
    setIsPlanning(true);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/time/quick-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ minutes: Number(quickMinutes) }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Quick plan failed.");
      }

      const data = await res.json();
      setQuickPlanResult(data.aiQuickPlan);
      setToast({ type: "success", title: `${quickMinutes}-Minute Plan Ready`, message: data.recommendedStrategy });
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    } finally {
      setIsPlanning(false);
    }
  };

  const handleRecalculateMissed = async () => {
    setIsPlanning(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/time/recalculate-missed", {
        method: "POST",
        credentials: "include",
      });

      if (res.ok) {
        const data = await res.json();
        setToast({ type: "warning", title: "Schedule Recalculated", message: data.recalculationStrategy });
        fetchSchedule();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: "Failed to recalculate missed tasks." });
    } finally {
      setIsPlanning(false);
    }
  };

  const handleBlockAction = async (blockId: string, action: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/time/blocks/${blockId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ action }),
      });

      if (res.ok) {
        setToast({ type: "success", title: "Action Applied", message: `Block updated: ${action}.` });
        fetchSchedule();
      }
    } catch (err) {
      setToast({ type: "error", title: "Error", message: `Failed to perform action ${action}.` });
    }
  };

  const getBlockIcon = (type: string) => {
    switch (type) {
      case "FOCUS": return <Target className="h-4 w-4 text-purple-400" />;
      case "LEARNING": return <BookOpen className="h-4 w-4 text-sky-400" />;
      case "BREAK": return <Coffee className="h-4 w-4 text-emerald-400" />;
      default: return <Clock className="h-4 w-4 text-amber-400" />;
    }
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Clock className="h-6 w-6 text-purple-400" />
            AI Time Management & Daily Planner
          </h1>
          <p className="text-xs text-muted-foreground">
            Multi-dimensional schedule optimization (revenue, deadlines, learning value, and available time).
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Switcher */}
          <div className="flex items-center rounded-xl glass-panel p-1 bg-secondary/30 border border-border/60">
            <button
              onClick={() => setViewMode("today")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === "today" ? "bg-primary text-white shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Today
            </button>
            <button
              onClick={() => setViewMode("week")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === "week" ? "bg-primary text-white shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Week
            </button>
            <button
              onClick={() => setViewMode("focus")}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === "focus" ? "bg-purple-600 text-white shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Zap className="h-3.5 w-3.5" /> Focus Mode
            </button>
          </div>

          <Button
            variant="primary"
            size="md"
            onClick={handlePlanMyDay}
            isLoading={isPlanning}
            leftIcon={<Sparkles className="h-4 w-4 text-purple-300" />}
          >
            AI Plan My Day
          </Button>
        </div>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* QUICK TIME BUDGET SCHEDULER: "I ONLY HAVE X MINUTES" */}
      <Card glass className="p-4 bg-gradient-to-r from-purple-900/20 via-card to-indigo-900/20 border-purple-500/30">
        <div className="flex flex-col md:flex-row items-md-center justify-between gap-4">
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-foreground flex items-center gap-2">
              <Zap className="h-4 w-4 text-purple-400" />
              "I Only Have X Minutes" Quick AI Scheduler
            </h4>
            <p className="text-xs text-muted-foreground">
              Got limited time right now? Tell AI how long you have, and it creates the highest-leverage sprint schedule.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 rounded-xl bg-secondary/50 px-3 py-1.5 border border-border/60">
              <span className="text-xs text-muted-foreground font-mono">Time Budget:</span>
              <input
                type="number"
                min={15}
                max={240}
                value={quickMinutes}
                onChange={(e) => setQuickMinutes(Number(e.target.value))}
                className="w-14 text-center font-mono font-bold text-xs bg-transparent text-purple-300 focus:outline-none"
              />
              <span className="text-xs text-muted-foreground font-mono">min</span>
            </div>

            <Button variant="secondary" size="sm" onClick={handleQuickPlan} isLoading={isPlanning}>
              Generate Quick Plan
            </Button>
          </div>
        </div>

        {quickPlanResult && (
          <div className="mt-3 p-3.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed">
            <span className="font-bold text-purple-300 block mb-1">Highest-Leverage {quickMinutes}-Minute Sprint Plan:</span>
            {quickPlanResult}
          </div>
        )}
      </Card>

      {/* VIEW 1 & 2: TODAY / WEEK SCHEDULE VIEW */}
      {viewMode !== "focus" && (
        <div className="space-y-6">
          {/* Top 3 Priorities Header */}
          <Card glass className="p-4 border-indigo-500/30">
            <div className="flex items-center justify-between border-b border-border/50 pb-2 mb-3">
              <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                <Target className="h-4 w-4 text-emerald-400" />
                Today's Top 3 Highest-Leverage Priorities
              </h3>

              <Button
                variant="outline"
                size="sm"
                onClick={handleRecalculateMissed}
                isLoading={isPlanning}
                leftIcon={<RefreshCw className="h-3.5 w-3.5 text-amber-400" />}
              >
                Intelligently Recalculate Missed Tasks
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {topPriorities.map((p, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-card/60 border border-border/50 text-xs font-mono text-indigo-300 font-bold">
                  {p}
                </div>
              ))}
            </div>
          </Card>

          {/* TimeBlocks Timeline */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <CalendarIcon className="h-4 w-4 text-sky-400" />
              Schedule Time Blocks ({timeBlocks.length})
            </h3>

            {timeBlocks.map((block) => (
              <Card key={block.id} glass className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-purple-500/40 transition-all">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-secondary/40 border border-border/60">
                    {getBlockIcon(block.blockType)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-foreground">{block.title}</h4>
                      <Badge variant={block.status === "COMPLETED" ? "completed" : "purple"}>
                        {block.status}
                      </Badge>
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">
                      {block.startTime} - {block.endTime} • <span className="uppercase text-purple-300">{block.blockType}</span>
                    </span>
                  </div>
                </div>

                {/* Action Suite: Complete, Skip, Reschedule, Split, Reduce Scope */}
                <div className="flex flex-wrap items-center gap-1.5">
                  <button
                    onClick={() => handleBlockAction(block.id, "COMPLETE")}
                    className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/30 text-[11px] font-mono font-bold flex items-center gap-1"
                    title="Complete Task"
                  >
                    <Check className="h-3.5 w-3.5" /> Done
                  </button>

                  <button
                    onClick={() => handleBlockAction(block.id, "SKIP")}
                    className="p-1.5 rounded-lg bg-secondary/50 text-slate-300 hover:bg-secondary border border-border/60 text-[11px] font-mono flex items-center gap-1"
                    title="Skip for Today"
                  >
                    Skip
                  </button>

                  <button
                    onClick={() => handleBlockAction(block.id, "RESCHEDULE")}
                    className="p-1.5 rounded-lg bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 border border-amber-500/30 text-[11px] font-mono flex items-center gap-1"
                    title="Reschedule Next Day"
                  >
                    Reschedule
                  </button>

                  <button
                    onClick={() => handleBlockAction(block.id, "SPLIT")}
                    className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 border border-indigo-500/30 text-[11px] font-mono flex items-center gap-1"
                    title="Split into 25-min micro-sprints"
                  >
                    <Scissors className="h-3.5 w-3.5" /> Split
                  </button>

                  <button
                    onClick={() => handleBlockAction(block.id, "REDUCE_SCOPE")}
                    className="p-1.5 rounded-lg bg-purple-500/10 text-purple-300 hover:bg-purple-500/20 border border-purple-500/30 text-[11px] font-mono flex items-center gap-1"
                    title="Reduce Scope"
                  >
                    <Minimize2 className="h-3.5 w-3.5" /> Reduce Scope
                  </button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* VIEW 3: DISTRACTION-FREE FOCUS MODE */}
      {viewMode === "focus" && (
        <Card glass className="p-8 text-center space-y-6 max-w-xl mx-auto border-purple-500/40 bg-gradient-to-b from-purple-950/20 via-card to-card">
          <div className="space-y-2">
            <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 text-xs font-mono font-bold">
              ACTIVE FOCUS SPRINT
            </span>
            <h2 className="text-xl font-bold text-foreground pt-1">
              Top Priority 1: High-Impact Focus Block
            </h2>
            <p className="text-xs text-muted-foreground">
              Distraction-free environment. Concentrate on high-leverage client deliverables.
            </p>
          </div>

          {/* Countdown Timer */}
          <div className="py-6">
            <span className="text-6xl font-extrabold text-white font-mono tracking-wider drop-shadow-lg">
              {formatTimer(focusSecondsLeft)}
            </span>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center gap-3">
            <Button
              variant="outline"
              size="md"
              onClick={() => setFocusSecondsLeft(1500)}
              leftIcon={<RefreshCw className="h-4 w-4" />}
            >
              Reset 25m
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={() => setToast({ type: "success", title: "Sprint Complete", message: "Great work!" })}
              leftIcon={<CheckCircle2 className="h-4 w-4 text-emerald-400" />}
            >
              Complete Sprint
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
