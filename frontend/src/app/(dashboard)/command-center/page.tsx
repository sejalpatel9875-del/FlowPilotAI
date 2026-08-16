"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { SystemStatusBar } from "@/components/mission-control/SystemStatusBar";
import { AgentConstellationGraph, AgentNodeData, FLEET_AGENTS } from "@/components/mission-control/AgentConstellationGraph";
import { AgentInspectorDrawer } from "@/components/mission-control/AgentInspectorDrawer";
import { LiveDecisionGate } from "@/components/mission-control/LiveDecisionGate";
import { AICommandCenter } from "@/components/command-center/AICommandCenter";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Toast, ToastType } from "@/components/ui/Toast";
import {
  Sparkles,
  Cpu,
  Zap,
  Bot,
  Activity,
  ShieldCheck,
  Play,
  ArrowRight,
  TrendingUp,
  Brain,
  Layers,
  CheckCircle2,
  Clock,
  ExternalLink,
} from "lucide-react";

export default function CommandCenterPage() {
  const router = useRouter();

  // Agent Selection & Inspector State
  const [selectedAgent, setSelectedAgent] = useState<AgentNodeData | null>(FLEET_AGENTS[0]);
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);

  // Recommendations State
  const [recommendations, setRecommendations] = useState<any[]>([]);
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
      setToast({ type: "success", title: "Fleet Evaluated", message: "Synthesized multi-agent priority matrix." });
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSelectAgent = (agent: AgentNodeData) => {
    setSelectedAgent(agent);
  };

  return (
    <div className="space-y-6">
      {/* 1. Top Mission Control Status Strip */}
      <SystemStatusBar
        activeAgentsCount={12}
        runningWorkflowsCount={3}
        pendingApprovalsCount={1}
        systemHealth={99.4}
      />

      {/* 2. Main Three-Zone Cockpit Architecture */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Left Zone: Natural Language Goal Dispatcher (5 cols) */}
        <div className="xl:col-span-5 space-y-5">
          <AICommandCenter />

          {/* Quick Autonomous Action Recommender */}
          <div className="p-5 rounded-2xl glass-panel bg-card/70 border border-border/80 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/15 text-primary">
                  <Brain className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider font-mono text-foreground">
                    Fleet Next Best Action
                  </h3>
                  <p className="text-[11px] text-muted-foreground">Multi-factor priority synthesizer</p>
                </div>
              </div>

              <Button
                variant="glass"
                size="sm"
                onClick={handleWhatShouldIDoNext}
                disabled={isAnalyzing}
                className="text-xs text-primary border-primary/30 hover:border-primary"
                leftIcon={<Sparkles className="h-3.5 w-3.5" />}
              >
                {isAnalyzing ? "Synthesizing..." : "Analyze Fleet"}
              </Button>
            </div>

            {aiAnalysisSummary && (
              <div className="p-3 rounded-xl bg-surface/70 border border-border/60 text-xs text-muted-foreground leading-relaxed">
                <div className="text-[10px] font-mono uppercase text-primary font-bold mb-1">
                  Executive Briefing:
                </div>
                {aiAnalysisSummary}
              </div>
            )}

            {recommendations.length > 0 && (
              <div className="space-y-2.5">
                {recommendations.slice(0, 2).map((rec, i) => (
                  <div
                    key={rec.id || i}
                    className="p-3 rounded-xl bg-surface/60 border border-border/50 hover:border-border transition-all space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-xs font-bold text-foreground">
                      <span>{rec.title}</span>
                      <Badge variant="default" size="sm">
                        {rec.priority || "HIGH"}
                      </Badge>
                    </div>
                    <p className="text-[11px] text-muted-foreground">{rec.reason}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Center & Right Zone: Central Constellation & Context Inspector (7 cols) */}
        <div className="xl:col-span-7 space-y-5 flex flex-col justify-between">
          {/* Central AI Network Constellation */}
          <AgentConstellationGraph
            selectedAgentName={selectedAgent?.name}
            onSelectAgent={handleSelectAgent}
          />

          {/* Dynamic Context Inspector for Selected Agent */}
          {selectedAgent && (
            <div className="p-5 rounded-2xl glass-panel bg-card/70 border border-border/80 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/15 text-primary border border-primary/30">
                    <Bot className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-foreground">{selectedAgent.name}</h4>
                      <Badge
                        variant={selectedAgent.status === "executing" ? "running" : "idle"}
                        size="sm"
                      >
                        {selectedAgent.status.toUpperCase()}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">{selectedAgent.role}</p>
                  </div>
                </div>

                <Button
                  variant="glass"
                  size="sm"
                  onClick={() => setIsInspectorOpen(true)}
                  className="text-xs text-foreground"
                  leftIcon={<ExternalLink className="h-3.5 w-3.5 text-primary" />}
                >
                  Full Inspector
                </Button>
              </div>

              {/* Live Task Strip */}
              <div className="p-3 rounded-xl bg-surface/70 border border-border/50 text-xs font-mono space-y-1">
                <span className="text-[10px] text-muted-foreground uppercase font-bold">Active Operation:</span>
                <div className="text-foreground">{selectedAgent.currentTask}</div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-3 font-mono text-center">
                <div className="p-2.5 rounded-xl bg-surface/50 border border-border/40">
                  <div className="text-[10px] text-muted-foreground uppercase">Confidence</div>
                  <div className="text-sm font-bold text-emerald-400">{selectedAgent.confidence}%</div>
                </div>
                <div className="p-2.5 rounded-xl bg-surface/50 border border-border/40">
                  <div className="text-[10px] text-muted-foreground uppercase">Token Usage</div>
                  <div className="text-sm font-bold text-primary">{selectedAgent.tokenUsage}</div>
                </div>
                <div className="p-2.5 rounded-xl bg-surface/50 border border-border/40">
                  <div className="text-[10px] text-muted-foreground uppercase">Latency</div>
                  <div className="text-sm font-bold text-sky-400">{selectedAgent.latencyMs} ms</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 3. Bottom Hero: Human Decision Gate Interface */}
      <LiveDecisionGate />

      {/* 4. Slide-out Agent Inspector Drawer */}
      <AgentInspectorDrawer
        agent={selectedAgent}
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
        onRunAgent={(name) => {
          setIsInspectorOpen(false);
          router.push(`/agents`);
        }}
      />

      {/* Toast Notification */}
      {toast && <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />}
    </div>
  );
}
