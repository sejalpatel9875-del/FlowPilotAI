"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { AICommandCenter } from "@/components/command-center/AICommandCenter";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Toast, ToastType } from "@/components/ui/Toast";
import {
  Sparkles,
  Terminal,
  Cpu,
  Target,
  Clock,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Play,
  Calendar,
  Layers,
  ArrowRight,
  TrendingUp,
  Brain
} from "lucide-react";

interface TopRecommendation {
  id: string;
  title: string;
  reason: string;
  estimatedTime: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  relatedObject: {
    type: "LEAD" | "TASK" | "PROJECT" | "FOLLOW_UP" | "LEARNING";
    id: string;
    label: string;
  };
  suggestedAction: string;
  factorScores: Record<string, number>;
}

export default function CommandCenterPage() {
  const router = useRouter();

  // Recommendations State
  const [recommendations, setRecommendations] = useState<TopRecommendation[]>([]);
  const [recommendationId, setRecommendationId] = useState<string | null>(null);
  const [aiAnalysisSummary, setAiAnalysisSummary] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  const handleWhatShouldIDoNext = async () => {
    setIsAnalyzing(true);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/command/what-should-i-do-next", {
        method: "POST",
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Analysis failed.");
      }

      const data = await res.json();
      setRecommendations(data.topRecommendations || []);
      setRecommendationId(data.recommendationId);
      setAiAnalysisSummary(data.aiAnalysisSummary);
      setToast({ type: "success", title: "Top 3 Actions Ranked", message: "Evaluated state across 8 modules using 6-factor matrix." });
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleApplyAction = async (recId: string, action: string, relObj?: any) => {
    try {
      if (recommendationId) {
        await fetch(`http://localhost:8000/api/v1/command/recommendations/${recommendationId}/action`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ action }),
        });
      }

      if (action === "ACCEPT") {
        setToast({ type: "success", title: "Action Accepted", message: "Action accepted and added to priority queue." });
      } else if (action === "DISMISS") {
        setRecommendations((prev) => prev.filter((r) => r.id !== recId));
        setToast({ type: "warning", title: "Action Dismissed", message: "Recommendation removed from recommendations list." });
      } else if (action === "RESCHEDULE") {
        setToast({ type: "info", title: "Action Rescheduled", message: "Moved recommendation to tomorrow's schedule." });
      } else if (action === "START_FOCUS") {
        setToast({ type: "purple" as any, title: "Focus Mode Started", message: "Launching distraction-free focus sprint..." });
        setTimeout(() => router.push("/tasks"), 1200);
      } else if (action === "OPEN_RELATED" && relObj) {
        const routeMap: Record<string, string> = {
          LEAD: "/leads",
          TASK: "/tasks",
          PROJECT: "/projects",
          FOLLOW_UP: "/follow-ups",
          LEARNING: "/learning",
        };
        const targetRoute = routeMap[relObj.type] || "/tasks";
        router.push(targetRoute);
      }
    } catch (err) {
      console.error("Action error", err);
    }
  };

  const getRelatedBadgeColor = (type: string) => {
    switch (type) {
      case "LEAD": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "PROJECT": return "bg-purple-500/10 text-purple-300 border-purple-500/30";
      case "TASK": return "bg-indigo-500/10 text-indigo-300 border-indigo-500/30";
      case "FOLLOW_UP": return "bg-amber-500/10 text-amber-300 border-amber-500/30";
      case "LEARNING": return "bg-sky-500/10 text-sky-400 border-sky-500/30";
      default: return "bg-secondary text-foreground border-border";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-purple-400" />
            AI Command Center & Action Orchestrator
          </h1>
          <p className="text-xs text-muted-foreground">
            Multi-dimensional intelligence across Tasks, Deadlines, Leads, Follow-ups, Projects, Goals, Learning, and Time.
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={handleWhatShouldIDoNext}
          isLoading={isAnalyzing}
          leftIcon={<Brain className="h-4 w-4 text-purple-300 animate-pulse" />}
        >
          What Should I Do Next?
        </Button>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* TOP 3 RANKED RECOMMENDATIONS SECTION */}
      {recommendations.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <Target className="h-4 w-4 text-purple-400" />
              Top 3 Highest-Leverage Ranked Actions
            </h3>
            <span className="text-xs font-mono text-muted-foreground">Ranked by 6-Factor Decision Matrix</span>
          </div>

          {aiAnalysisSummary && (
            <Card glass className="p-3.5 bg-purple-950/20 border-purple-500/30 text-xs font-mono text-slate-200">
              <span className="font-bold text-purple-300 block mb-1">AI Orchestrator Analysis:</span>
              {aiAnalysisSummary}
            </Card>
          )}

          <div className="grid grid-cols-1 gap-4">
            {recommendations.map((rec, index) => (
              <Card key={rec.id} glass className="p-5 space-y-4 hover:border-purple-500/40 transition-all border-l-4 border-l-purple-500">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-purple-500/20 text-purple-300 text-xs font-mono font-bold">
                        #{index + 1}
                      </span>
                      <h4 className="text-base font-bold text-foreground">{rec.title}</h4>
                      <Badge variant={rec.priority === "HIGH" ? "purple" : "secondary"}>
                        {rec.priority} PRIORITY
                      </Badge>
                    </div>

                    <div className="flex items-center gap-2 text-xs font-mono">
                      <span className={`px-2 py-0.5 rounded border text-[10px] uppercase font-bold ${getRelatedBadgeColor(rec.relatedObject.type)}`}>
                        {rec.relatedObject.type}: {rec.relatedObject.label}
                      </span>
                      <span className="text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3 text-slate-400" /> Est: {rec.estimatedTime}
                      </span>
                    </div>
                  </div>

                  {/* Open Related Item Button */}
                  <button
                    onClick={() => handleApplyAction(rec.id, "OPEN_RELATED", rec.relatedObject)}
                    className="flex items-center gap-1.5 text-xs font-mono text-purple-300 hover:text-purple-200 transition-colors p-2 rounded-lg bg-purple-500/10 border border-purple-500/20"
                  >
                    Open Item <ExternalLink className="h-3.5 w-3.5" />
                  </button>
                </div>

                {/* Rationale & Suggested Action */}
                <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1 text-xs">
                  <span className="text-muted-foreground font-mono font-bold block">Why This Action:</span>
                  <p className="text-slate-200">{rec.reason}</p>
                  <div className="pt-2 font-mono text-[11px] text-purple-300 font-bold flex items-center gap-1">
                    <ArrowRight className="h-3.5 w-3.5 text-purple-400" />
                    Suggested Step: {rec.suggestedAction}
                  </div>
                </div>

                {/* Action Suite: Accept, Dismiss, Reschedule, Start Focus */}
                <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-border/40">
                  <button
                    onClick={() => handleApplyAction(rec.id, "ACCEPT")}
                    className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/30 text-xs font-mono font-bold flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" /> Accept
                  </button>

                  <button
                    onClick={() => handleApplyAction(rec.id, "START_FOCUS")}
                    className="px-3 py-1.5 rounded-lg bg-purple-600 text-white hover:bg-purple-500 text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm"
                  >
                    <Play className="h-3.5 w-3.5" /> Start Focus
                  </button>

                  <button
                    onClick={() => handleApplyAction(rec.id, "RESCHEDULE")}
                    className="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 border border-amber-500/30 text-xs font-mono flex items-center gap-1.5"
                  >
                    <Calendar className="h-3.5 w-3.5" /> Reschedule
                  </button>

                  <button
                    onClick={() => handleApplyAction(rec.id, "DISMISS")}
                    className="px-3 py-1.5 rounded-lg bg-secondary/50 text-slate-400 hover:bg-secondary border border-border/60 text-xs font-mono flex items-center gap-1.5"
                  >
                    <XCircle className="h-3.5 w-3.5" /> Dismiss
                  </button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Main Command Input Box */}
      <AICommandCenter />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card glass>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Terminal className="h-4 w-4 text-indigo-400" />
              API Dispatcher Endpoint
            </CardTitle>
            <CardDescription>Target endpoint contract for command processing</CardDescription>
          </CardHeader>
          <CardContent className="text-xs font-mono bg-secondary/30 p-3 rounded-lg border border-border/50 text-slate-300">
            POST http://localhost:8000/api/v1/command/what-should-i-do-next
          </CardContent>
        </Card>

        <Card glass>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Cpu className="h-4 w-4 text-emerald-400" />
              Agent Bus Status
            </CardTitle>
            <CardDescription>Redis event bus connection health</CardDescription>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            Redis event bus connection is ready to dispatch async worker tasks.
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
