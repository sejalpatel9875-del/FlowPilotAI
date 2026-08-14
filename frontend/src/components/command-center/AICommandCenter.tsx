"use client";

import React, { useState } from "react";
import { cn } from "@/utils/cn";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { CommandPromptResponse } from "@/types";
import { apiService } from "@/services/api";
import {
  Sparkles,
  Send,
  RefreshCw,
  AlertCircle,
  Lightbulb,
  CheckCircle2,
  ArrowRight,
  Bot
} from "lucide-react";

export interface AICommandCenterProps {
  className?: string;
}

export const suggestedPrompts = [
  "What should I focus on next?",
  "Draft a follow-up email for stale lead pipeline",
  "Summarize upcoming client project deadlines for this week",
  "Identify high-value leads requiring immediate outreach",
];

export const AICommandCenter: React.FC<AICommandCenterProps> = ({ className }) => {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [response, setResponse] = useState<CommandPromptResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmitPrompt = async (promptText: string) => {
    if (!promptText.trim()) return;
    setQuery(promptText);
    setStatus("loading");
    setErrorMessage(null);

    try {
      const result = await apiService.sendCommand({ query: promptText });
      setResponse(result);
      setStatus("success");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to reach AI Command Dispatcher service.");
      setStatus("error");
    }
  };

  return (
    <Card glass className={cn("relative overflow-hidden border-indigo-500/20 bg-gradient-to-b from-card via-card to-indigo-950/20", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 shadow-glow-purple">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-foreground">AI Command Center</CardTitle>
              <CardDescription>Intelligent orchestrator for freelancing workflows & task prioritization</CardDescription>
            </div>
          </div>
          <span className="hidden sm:inline-flex px-2.5 py-1 text-[10px] font-mono font-semibold rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
            API Dispatcher Ready
          </span>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Input Console */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmitPrompt(query);
          }}
          className="relative flex items-center"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What should I focus on next?"
            className="w-full rounded-xl glass-panel bg-secondary/40 pl-4 pr-24 py-3.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 shadow-inner"
          />
          <div className="absolute right-2 flex items-center gap-1.5">
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={status === "loading"}
              disabled={!query.trim()}
              leftIcon={<Send className="h-3.5 w-3.5" />}
            >
              Dispatch
            </Button>
          </div>
        </form>

        {/* Suggested Prompts */}
        <div className="space-y-1.5">
          <span className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
            <Lightbulb className="h-3 w-3 text-amber-400" />
            Suggested Prompts:
          </span>
          <div className="flex flex-wrap gap-2">
            {suggestedPrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSubmitPrompt(prompt)}
                className="text-xs px-3 py-1.5 rounded-lg glass-panel bg-secondary/30 hover:bg-card-hover border-border/60 text-muted-foreground hover:text-foreground transition-all text-left"
              >
                "{prompt}"
              </button>
            ))}
          </div>
        </div>

        {/* Loading State */}
        {status === "loading" && (
          <div className="p-5 rounded-xl border border-purple-500/20 bg-purple-950/10 space-y-3 animate-fade-in">
            <div className="flex items-center gap-2 text-xs font-semibold text-purple-300">
              <Bot className="h-4 w-4 animate-spin text-purple-400" />
              <span>Analyzing workspace signals & dispatching agent planner...</span>
            </div>
            <Skeleton className="h-4 w-3/4 bg-purple-500/20" />
            <Skeleton className="h-4 w-1/2 bg-purple-500/20" />
          </div>
        )}

        {/* Response State */}
        {status === "success" && response && (
          <div className="p-5 rounded-xl border border-indigo-500/30 bg-indigo-950/20 space-y-4 animate-fade-in text-xs">
            <div className="flex items-center justify-between border-b border-indigo-500/20 pb-3">
              <div className="flex items-center gap-2 text-indigo-300 font-semibold">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                <span>Command Execution Plan Generated</span>
              </div>
              <span className="text-[10px] font-mono text-muted-foreground">{response.timestamp}</span>
            </div>

            <div className="space-y-1">
              <span className="text-muted-foreground text-[10px] uppercase tracking-wider font-semibold">Primary Recommendation</span>
              <p className="text-sm font-semibold text-foreground">{response.suggestedAction}</p>
            </div>

            {response.reasoning && response.reasoning.length > 0 && (
              <div className="space-y-1">
                <span className="text-muted-foreground text-[10px] uppercase tracking-wider font-semibold">Reasoning & Signals</span>
                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                  {response.reasoning.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}

            {response.recommendedSteps && response.recommendedSteps.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-indigo-500/20">
                <span className="text-muted-foreground text-[10px] uppercase tracking-wider font-semibold">Action Steps</span>
                <div className="grid gap-2 sm:grid-cols-2">
                  {response.recommendedSteps.map((step, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-card/80 border border-border/60 flex flex-col justify-between">
                      <div>
                        <span className="font-semibold text-foreground block">{step.title}</span>
                        <p className="text-[11px] text-muted-foreground mt-0.5">{step.description}</p>
                      </div>
                      {step.agentToAssign && (
                        <div className="mt-2 flex items-center justify-between text-[10px]">
                          <span className="text-purple-400 font-mono">Agent: {step.agentToAssign}</span>
                          <ArrowRight className="h-3 w-3 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error State */}
        {status === "error" && (
          <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-950/20 text-rose-300 text-xs flex items-start gap-3 animate-fade-in">
            <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1 space-y-1">
              <h5 className="font-semibold text-rose-200">Dispatcher Service Error</h5>
              <p className="text-rose-300/80">{errorMessage}</p>
              <button
                onClick={() => handleSubmitPrompt(query)}
                className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-rose-200 underline hover:text-white"
              >
                <RefreshCw className="h-3 w-3" /> Retry Dispatch
              </button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
