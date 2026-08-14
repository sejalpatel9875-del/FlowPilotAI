"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Tabs } from "@/components/ui/Tabs";
import {
  Sparkles,
  Play,
  Cpu,
  Sliders,
  Terminal,
  Activity,
  Layers,
  Clock,
  Coins,
  ShieldCheck,
  Send
} from "lucide-react";

export default function AIPlaygroundPage() {
  const [prompt, setPrompt] = useState("Explain how FlowPilot AI automates freelance client outreach.");
  const [systemPrompt, setSystemPrompt] = useState("You are an expert AI productivity assistant.");
  const [provider, setProvider] = useState("local");
  const [model, setModel] = useState("flowpilot-local-v1");
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isStructured, setIsStructured] = useState(false);

  const [output, setOutput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [diagnostics, setDiagnostics] = useState<any>(null);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  const handleExecute = async () => {
    if (!prompt.trim()) return;

    setIsLoading(true);
    setOutput("");
    setDiagnostics(null);
    setToast(null);

    const startTime = performance.now();

    try {
      if (isStreaming) {
        const res = await fetch("http://localhost:8000/api/v1/ai/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            prompt,
            provider,
            model,
            systemPrompt,
            temperature,
            maxTokens,
          }),
        });

        if (!res.ok) {
          throw new Error(`HTTP Error ${res.status}: ${await res.text()}`);
        }

        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        let accumulated = "";

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            const lines = chunk.split("\n\n");
            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const data = line.slice(6);
                if (data === "[DONE]") break;
                accumulated += data;
                setOutput(accumulated);
              }
            }
          }
        }

        const endTime = performance.now();
        setDiagnostics({
          requestId: `stream_${Math.random().toString(36).substring(7)}`,
          latencyMs: Math.round(endTime - startTime),
          provider,
          model,
          mode: "Streaming SSE",
        });

      } else if (isStructured) {
        const res = await fetch("http://localhost:8000/api/v1/ai/structured", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            prompt,
            responseSchema: { suggestedAction: "string", confidenceScore: "number" },
            provider,
            model,
          }),
        });

        if (!res.ok) throw new Error("Structured output error.");
        const data = await res.json();
        setOutput(JSON.stringify(data, null, 2));

        const endTime = performance.now();
        setDiagnostics({
          requestId: `struct_${Math.random().toString(36).substring(7)}`,
          latencyMs: Math.round(endTime - startTime),
          provider,
          model,
          mode: "Structured JSON",
        });

      } else {
        const res = await fetch("http://localhost:8000/api/v1/ai/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            prompt,
            provider,
            model,
            systemPrompt,
            temperature,
            maxTokens,
          }),
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Generation error.");
        }

        const data = await res.json();
        setOutput(data.text);
        setDiagnostics({
          requestId: data.requestId,
          latencyMs: Math.round(performance.now() - startTime),
          provider: data.provider,
          model: data.model,
          usage: data.usage,
          mode: "Standard Completion",
        });
      }
    } catch (err: any) {
      setToast({ type: "error", title: "LLM Gateway Error", message: err.message });
      setOutput(`[Execution Error]: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-purple-400" />
            AI LLM Gateway Playground
          </h1>
          <p className="text-xs text-muted-foreground">
            Provider-independent LLM testing suite supporting OpenAI, Anthropic, Gemini & Local engines.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="completed" className="font-mono">
            <ShieldCheck className="h-3 w-3 mr-1" />
            Authenticated Session Active
          </Badge>
        </div>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Main Grid: Controls & Prompt vs Output */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (1 Col): Hyperparameters & Controls */}
        <Card glass className="space-y-4">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sliders className="h-4 w-4 text-indigo-400" />
              Gateway Parameters
            </CardTitle>
            <CardDescription>Select model provider, streaming mode, and sampling parameters</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4 text-xs">
            {/* Provider Selection */}
            <div className="space-y-1">
              <label className="font-medium text-foreground">LLM Provider</label>
              <select
                value={provider}
                onChange={(e) => {
                  setProvider(e.target.value);
                  if (e.target.value === "openai") setModel("gpt-4o");
                  else if (e.target.value === "nvidia") setModel("nvidia/nemotron-3-ultra-550b-a55b");
                  else if (e.target.value === "anthropic") setModel("claude-3-5-sonnet-20240620");
                  else if (e.target.value === "gemini") setModel("gemini-1.5-pro");
                  else setModel("flowpilot-local-v1");
                }}
                className="w-full rounded-xl glass-panel bg-secondary/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
              >
                <option value="local">FlowPilot Local Engine (Fail-Safe Dev)</option>
                <option value="nvidia">NVIDIA NIM Gateway</option>
                <option value="openai">OpenAI Adapter</option>
                <option value="anthropic">Anthropic Claude Adapter</option>
                <option value="gemini">Google Gemini Adapter</option>
              </select>
            </div>

            {/* Model Name */}
            <div className="space-y-1">
              <label className="font-medium text-foreground">Target Model</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full rounded-xl glass-panel bg-secondary/40 px-3 py-2 text-xs text-foreground font-mono focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
              />
            </div>

            {/* Temperature */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="font-medium text-foreground">Temperature</label>
                <span className="font-mono text-muted-foreground">{temperature}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-primary"
              />
            </div>

            {/* Max Tokens */}
            <div className="space-y-1">
              <label className="font-medium text-foreground">Max Tokens</label>
              <input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value) || 500)}
                className="w-full rounded-xl glass-panel bg-secondary/40 px-3 py-2 text-xs text-foreground font-mono focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
              />
            </div>

            {/* Execution Toggles */}
            <div className="pt-2 border-t border-border/50 space-y-2">
              <label className="flex items-center justify-between cursor-pointer">
                <span className="font-medium text-foreground">Streaming SSE</span>
                <input
                  type="checkbox"
                  checked={isStreaming}
                  onChange={(e) => {
                    setIsStreaming(e.target.checked);
                    if (e.target.checked) setIsStructured(false);
                  }}
                  className="rounded border-border accent-primary h-4 w-4"
                />
              </label>

              <label className="flex items-center justify-between cursor-pointer">
                <span className="font-medium text-foreground">Structured JSON Output</span>
                <input
                  type="checkbox"
                  checked={isStructured}
                  onChange={(e) => {
                    setIsStructured(e.target.checked);
                    if (e.target.checked) setIsStreaming(false);
                  }}
                  className="rounded border-border accent-primary h-4 w-4"
                />
              </label>
            </div>

            <Button
              variant="primary"
              size="md"
              onClick={handleExecute}
              isLoading={isLoading}
              className="w-full mt-3 font-semibold"
              rightIcon={<Send className="h-4 w-4" />}
            >
              Dispatch Prompt
            </Button>
          </CardContent>
        </Card>

        {/* Right Column (2 Cols): Prompt Console & Output Response */}
        <div className="lg:col-span-2 space-y-6">
          {/* Prompts Input */}
          <Card glass>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Terminal className="h-4 w-4 text-purple-400" />
                Prompt Construction
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="font-medium text-muted-foreground">System Prompt</label>
                <input
                  type="text"
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  className="w-full rounded-xl glass-panel bg-secondary/30 px-3.5 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/60"
                />
              </div>

              <div className="space-y-1">
                <label className="font-medium text-muted-foreground">User Prompt</label>
                <textarea
                  rows={4}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="w-full rounded-xl glass-panel bg-secondary/40 p-3.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80 resize-none"
                />
              </div>
            </CardContent>
          </Card>

          {/* Response & Diagnostics */}
          <Card glass className="border-purple-500/20">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="h-4 w-4 text-emerald-400" />
                  Response Output
                </CardTitle>
                <CardDescription>Generated text or JSON payload from LLM Gateway</CardDescription>
              </div>

              {diagnostics && (
                <div className="flex items-center gap-3 text-[10px] font-mono text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3 text-sky-400" />
                    {diagnostics.latencyMs}ms
                  </span>
                  {diagnostics.usage && (
                    <span className="flex items-center gap-1">
                      <Coins className="h-3 w-3 text-amber-400" />
                      {diagnostics.usage.totalTokens} Tokens
                    </span>
                  )}
                </div>
              )}
            </CardHeader>

            <CardContent className="space-y-3">
              <div className="min-h-[160px] p-4 rounded-xl glass-panel bg-secondary/30 border border-border/60 font-mono text-xs text-slate-200 whitespace-pre-wrap overflow-x-auto">
                {isLoading && !output && (
                  <div className="flex items-center gap-2 text-purple-400">
                    <Cpu className="h-4 w-4 animate-spin" />
                    <span>Streaming LLM Gateway tokens...</span>
                  </div>
                )}
                {output || <span className="text-muted-foreground italic">Response output will stream here after dispatching.</span>}
              </div>

              {diagnostics && (
                <div className="p-3 rounded-xl bg-card/60 border border-border/50 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
                  <div>
                    <span className="text-muted-foreground block">Request ID</span>
                    <span className="text-indigo-400 font-bold truncate block">{diagnostics.requestId}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Provider</span>
                    <span className="text-emerald-400 font-bold block">{diagnostics.provider}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Latency</span>
                    <span className="text-sky-400 font-bold block">{diagnostics.latencyMs} ms</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Mode</span>
                    <span className="text-purple-400 font-bold block">{diagnostics.mode}</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
