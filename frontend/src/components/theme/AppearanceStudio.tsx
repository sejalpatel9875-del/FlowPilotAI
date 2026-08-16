"use client";

import React, { useState, useEffect } from "react";
import { useTheme } from "@/app/providers";
import { THEME_PRESETS } from "@/utils/themePresets";
import { ACCENT_COLOR_MAP, AI_CORE_COLOR_MAP } from "@/utils/tokenGenerator";
import {
  PresetMode,
  BackgroundMode,
  AccentColor,
  AICoreColor,
  AgentGlowMode,
  GlassIntensity,
  BorderIntensity,
  MotionPreset,
  BackgroundEffect,
  Density,
} from "@/types/theme";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  Sparkles,
  X,
  RotateCcw,
  Sliders,
  Palette,
  Layers,
  Save,
  Download,
  Upload,
  Check,
  Zap,
  Activity,
  Bot,
  ArrowRight,
  Sun,
  Moon,
  Copy,
  Eye,
  Trash2,
  Edit2,
} from "lucide-react";

export const AppearanceStudio: React.FC = () => {
  const {
    isStudioOpen,
    closeStudio,
    themeConfig,
    setThemeConfig,
    updateThemeProperty,
    applyPreset,
    savedThemes,
    saveCustomTheme,
    deleteCustomTheme,
    exportThemeJson,
    importThemeJson,
    resetToDefaults,
  } = useTheme();

  const [activeTab, setActiveTab] = useState<"presets" | "builder" | "saved">("presets");
  const [importJsonText, setImportJsonText] = useState("");
  const [importFeedback, setImportFeedback] = useState<{ success: boolean; message: string } | null>(null);
  const [copiedNotification, setCopiedNotification] = useState(false);
  const [namingSlotId, setNamingSlotId] = useState<string | null>(null);
  const [customThemeName, setCustomThemeName] = useState("");

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isStudioOpen) {
        closeStudio();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isStudioOpen, closeStudio]);

  if (!isStudioOpen) return null;

  // Smart Adaptive Checks
  const hour = new Date().getHours();
  const isEvening = hour >= 19 || hour < 7;
  const isReducedMotionPreferred =
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const handleCopyJson = () => {
    const jsonStr = exportThemeJson();
    navigator.clipboard.writeText(jsonStr);
    setCopiedNotification(true);
    setTimeout(() => setCopiedNotification(false), 2500);
  };

  const handleDownloadJson = () => {
    const jsonStr = exportThemeJson();
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `flowpilot-theme-${themeConfig.preset}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = () => {
    const result = importThemeJson(importJsonText);
    setImportFeedback(result);
    if (result.success) {
      setTimeout(() => {
        setImportFeedback(null);
        setImportJsonText("");
      }, 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="relative flex flex-col w-full max-w-5xl max-h-[92vh] rounded-2xl glass-panel bg-card/95 border border-border/80 shadow-2xl overflow-hidden"
        style={{ backdropFilter: "blur(24px)" }}
      >
        {/* Top Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/60 bg-surface-low/50">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-primary to-secondary text-white shadow-md glow-primary">
              <Sliders className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold tracking-tight text-foreground">
                  Adaptive Appearance Studio
                </h2>
                <Badge variant="default" size="sm">
                  {themeConfig.preset.toUpperCase()}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                Real-time visual personalization, design tokens & ambient motion engine
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={resetToDefaults}
              className="text-xs text-muted-foreground hover:text-foreground"
              leftIcon={<RotateCcw className="h-3.5 w-3.5" />}
            >
              Reset
            </Button>
            <button
              onClick={closeStudio}
              aria-label="Close Studio"
              className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-card-hover hover:text-foreground transition-all"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Smart Recommendations Bar */}
        <div className="flex flex-wrap items-center gap-2 px-6 py-2.5 bg-surface-lowest/70 border-b border-border/40 text-xs">
          <div className="flex items-center gap-1.5 font-semibold text-primary">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Adaptive Insight:</span>
          </div>

          {isEvening && themeConfig.preset !== "obsidian" && themeConfig.preset !== "midnight" && (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
              <Moon className="h-3 w-3" />
              <span>Evening detected. Relaxed night contrast recommended.</span>
              <button
                onClick={() => applyPreset("obsidian")}
                className="ml-1 text-[11px] font-bold text-white underline hover:no-underline"
              >
                Apply Obsidian
              </button>
            </div>
          )}

          {isReducedMotionPreferred && themeConfig.motion !== "off" && (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300">
              <Zap className="h-3 w-3" />
              <span>System prefers reduced motion.</span>
              <button
                onClick={() => updateThemeProperty("motion", "off")}
                className="ml-1 text-[11px] font-bold text-white underline hover:no-underline"
              >
                Disable Motion
              </button>
            </div>
          )}

          <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
            <Activity className="h-3 w-3" />
            <span>High Readability:</span>
            <button
              onClick={() => applyPreset("focus")}
              className="text-[11px] font-bold text-white underline hover:no-underline"
            >
              Switch to Focus Mode
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center justify-between px-6 pt-3 border-b border-border/50 bg-card/40">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("presets")}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-t-xl transition-all ${
                activeTab === "presets"
                  ? "bg-card border-t border-x border-border text-primary border-b-2 border-b-primary shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Palette className="h-3.5 w-3.5" />
              <span>Presets ({Object.keys(THEME_PRESETS).length})</span>
            </button>

            <button
              onClick={() => setActiveTab("builder")}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-t-xl transition-all ${
                activeTab === "builder"
                  ? "bg-card border-t border-x border-border text-primary border-b-2 border-b-primary shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Sliders className="h-3.5 w-3.5" />
              <span>Custom Builder</span>
            </button>

            <button
              onClick={() => setActiveTab("saved")}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-t-xl transition-all ${
                activeTab === "saved"
                  ? "bg-card border-t border-x border-border text-primary border-b-2 border-b-primary shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              <span>Saved Slots & Portability</span>
            </button>
          </div>

          <div className="text-[11px] font-mono text-muted-foreground hidden sm:block">
            Instant Preview • Zero Reload
          </div>
        </div>

        {/* Main Content Body */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-y-auto p-4 sm:p-6 gap-6">
          {/* Left Column: Controls (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* TAB 1: PRESET CARDS */}
            {activeTab === "presets" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {(Object.entries(THEME_PRESETS) as [PresetMode, (typeof THEME_PRESETS)[PresetMode]][]).map(
                  ([key, preset]) => {
                    const isActive = themeConfig.preset === key;
                    return (
                      <button
                        key={key}
                        onClick={() => applyPreset(key)}
                        className={`flex flex-col text-left p-4 rounded-xl transition-all border ${
                          isActive
                            ? "bg-primary/10 border-primary ring-1 ring-primary/50 shadow-md"
                            : "bg-surface/60 hover:bg-card-hover border-border/60 hover:border-border"
                        }`}
                      >
                        <div className="flex items-center justify-between w-full mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-foreground">
                              {preset.name}
                            </span>
                            <Badge variant={isActive ? "default" : "outline"} size="sm">
                              {preset.badge}
                            </Badge>
                          </div>
                          {/* Mini Color Chips */}
                          <div className="flex items-center gap-1">
                            <span
                              className="h-3 w-3 rounded-full border border-white/20"
                              style={{ backgroundColor: preset.previewColors.bg }}
                            />
                            <span
                              className="h-3 w-3 rounded-full border border-white/20"
                              style={{ backgroundColor: preset.previewColors.accent }}
                            />
                            <span
                              className="h-3 w-3 rounded-full border border-white/20"
                              style={{ backgroundColor: preset.previewColors.aiCore }}
                            />
                          </div>
                        </div>

                        <p className="text-[11px] text-muted-foreground line-clamp-2">
                          {preset.description}
                        </p>
                      </button>
                    );
                  }
                )}
              </div>
            )}

            {/* TAB 2: CUSTOM BUILDER */}
            {activeTab === "builder" && (
              <div className="space-y-5">
                {/* 1. Background Mode */}
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                    Background Environment
                  </label>
                  <div className="grid grid-cols-4 gap-2">
                    {(["dark", "light", "warm", "custom"] as BackgroundMode[]).map((mode) => (
                      <button
                        key={mode}
                        onClick={() => updateThemeProperty("background", mode)}
                        className={`px-3 py-2 rounded-xl text-xs font-semibold capitalize border transition-all ${
                          themeConfig.background === mode
                            ? "bg-primary text-white border-primary shadow-sm"
                            : "bg-surface/70 text-foreground border-border/70 hover:bg-card-hover"
                        }`}
                      >
                        {mode}
                      </button>
                    ))}
                  </div>
                  {themeConfig.background === "custom" && (
                    <div className="mt-2 flex items-center gap-3">
                      <input
                        type="color"
                        value={themeConfig.customBackgroundHex || "#05070B"}
                        onChange={(e) => updateThemeProperty("customBackgroundHex", e.target.value)}
                        className="h-8 w-12 cursor-pointer rounded border border-border bg-transparent"
                      />
                      <span className="text-xs font-mono text-muted-foreground">
                        {themeConfig.customBackgroundHex || "#05070B"}
                      </span>
                    </div>
                  )}
                </div>

                {/* 2. Primary Accent */}
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                    Primary Accent Color
                  </label>
                  <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
                    {(Object.keys(ACCENT_COLOR_MAP) as AccentColor[]).map((acc) => (
                      <button
                        key={acc}
                        onClick={() => updateThemeProperty("primaryAccent", acc)}
                        className={`flex flex-col items-center gap-1.5 p-2 rounded-xl border transition-all ${
                          themeConfig.primaryAccent === acc
                            ? "border-primary bg-primary/15 ring-1 ring-primary"
                            : "border-border/60 bg-surface/50 hover:bg-card-hover"
                        }`}
                      >
                        <span
                          className="h-4 w-4 rounded-full border border-white/20 shadow-sm"
                          style={{ backgroundColor: ACCENT_COLOR_MAP[acc].hex }}
                        />
                        <span className="text-[10px] font-medium capitalize text-muted-foreground">
                          {acc}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* 3. AI Core Color */}
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                    AI Core Energy & Orb Color
                  </label>
                  <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
                    {(Object.keys(AI_CORE_COLOR_MAP) as AICoreColor[]).map((core) => (
                      <button
                        key={core}
                        onClick={() => updateThemeProperty("aiCoreColor", core)}
                        className={`flex flex-col items-center gap-1.5 p-2 rounded-xl border transition-all ${
                          themeConfig.aiCoreColor === core
                            ? "border-primary bg-primary/15 ring-1 ring-primary"
                            : "border-border/60 bg-surface/50 hover:bg-card-hover"
                        }`}
                      >
                        <span
                          className="h-4 w-4 rounded-full border border-white/20 shadow-sm"
                          style={{
                            backgroundColor: AI_CORE_COLOR_MAP[core].hex,
                            boxShadow: `0 0 8px ${AI_CORE_COLOR_MAP[core].hex}`,
                          }}
                        />
                        <span className="text-[10px] font-medium capitalize text-muted-foreground">
                          {core}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* 4. Motion Preset */}
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                    Motion & Spatial Dynamics
                  </label>
                  <div className="grid grid-cols-4 gap-2">
                    {(["off", "subtle", "cinematic", "immersive"] as MotionPreset[]).map((m) => (
                      <button
                        key={m}
                        onClick={() => updateThemeProperty("motion", m)}
                        className={`px-3 py-2 rounded-xl text-xs font-semibold capitalize border transition-all ${
                          themeConfig.motion === m
                            ? "bg-primary text-white border-primary shadow-sm"
                            : "bg-surface/70 text-foreground border-border/70 hover:bg-card-hover"
                        }`}
                      >
                        {m}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 5. Background Effect & Density */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                      Atmospheric Canvas Effect
                    </label>
                    <select
                      value={themeConfig.backgroundEffect}
                      onChange={(e) => updateThemeProperty("backgroundEffect", e.target.value as BackgroundEffect)}
                      className="w-full px-3 py-2 rounded-xl bg-surface/80 border border-border text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    >
                      <option value="none">None (Pure Color)</option>
                      <option value="grid">Perspective Grid</option>
                      <option value="particles">Neural Particle Mesh</option>
                      <option value="aurora">Cosmic Aurora Glow</option>
                      <option value="ambient_glow">Ambient Corner Glow</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                      Information Density
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {(["comfortable", "compact"] as Density[]).map((d) => (
                        <button
                          key={d}
                          onClick={() => updateThemeProperty("density", d)}
                          className={`px-3 py-2 rounded-xl text-xs font-semibold capitalize border transition-all ${
                            themeConfig.density === d
                              ? "bg-primary text-white border-primary"
                              : "bg-surface/70 text-foreground border-border/70 hover:bg-card-hover"
                          }`}
                        >
                          {d}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 6. Glass & Border Intensity */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                      Glass Intensity
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {(["minimal", "balanced", "strong"] as GlassIntensity[]).map((g) => (
                        <button
                          key={g}
                          onClick={() => updateThemeProperty("glassIntensity", g)}
                          className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold capitalize border transition-all ${
                            themeConfig.glassIntensity === g
                              ? "bg-primary text-white border-primary"
                              : "bg-surface/70 text-foreground border-border/70"
                          }`}
                        >
                          {g}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                      Border Intensity
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {(["subtle", "standard", "strong"] as BorderIntensity[]).map((b) => (
                        <button
                          key={b}
                          onClick={() => updateThemeProperty("borderIntensity", b)}
                          className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold capitalize border transition-all ${
                            themeConfig.borderIntensity === b
                              ? "bg-primary text-white border-primary"
                              : "bg-surface/70 text-foreground border-border/70"
                          }`}
                        >
                          {b}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: SAVED THEMES & PORTABILITY */}
            {activeTab === "saved" && (
              <div className="space-y-6">
                {/* Saved Custom Slots */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Personalized Custom Slots ({savedThemes.length})
                    </label>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => saveCustomTheme(customThemeName || `Custom Theme ${savedThemes.length + 1}`, themeConfig)}
                      leftIcon={<Save className="h-3.5 w-3.5" />}
                    >
                      Save Current Configuration
                    </Button>
                  </div>

                  <div className="space-y-2.5">
                    {savedThemes.map((st) => (
                      <div
                        key={st.id}
                        className="flex items-center justify-between p-3.5 rounded-xl bg-surface/70 border border-border/70 hover:border-border transition-all"
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className="h-6 w-6 rounded-lg border border-white/20 flex items-center justify-center text-[10px] font-bold text-white shadow-sm"
                            style={{ backgroundColor: ACCENT_COLOR_MAP[st.config.primaryAccent]?.hex || "#2E7BFF" }}
                          >
                            <Palette className="h-3.5 w-3.5" />
                          </div>
                          <div>
                            {namingSlotId === st.id ? (
                              <input
                                type="text"
                                defaultValue={st.name}
                                onBlur={(e) => {
                                  saveCustomTheme(e.target.value, st.config, st.id);
                                  setNamingSlotId(null);
                                }}
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") {
                                    saveCustomTheme((e.target as HTMLInputElement).value, st.config, st.id);
                                    setNamingSlotId(null);
                                  }
                                }}
                                autoFocus
                                className="px-2 py-0.5 rounded bg-surface-container border border-primary text-xs text-foreground"
                              />
                            ) : (
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-foreground">{st.name}</span>
                                <button
                                  onClick={() => setNamingSlotId(st.id)}
                                  className="text-muted-foreground hover:text-foreground"
                                >
                                  <Edit2 className="h-3 w-3" />
                                </button>
                              </div>
                            )}
                            <div className="text-[10px] text-muted-foreground capitalize">
                              {st.config.background} • {st.config.primaryAccent} • {st.config.motion} motion
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setThemeConfig({ ...st.config, preset: "custom" })}
                            leftIcon={<Eye className="h-3.5 w-3.5" />}
                          >
                            Load
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteCustomTheme(st.id)}
                            className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Import / Export JSON */}
                <div className="p-4 rounded-xl bg-surface-lowest/80 border border-border/60 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-foreground">Portable Theme JSON</span>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="glass"
                        size="sm"
                        onClick={handleCopyJson}
                        leftIcon={copiedNotification ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                      >
                        {copiedNotification ? "Copied!" : "Copy JSON"}
                      </Button>
                      <Button
                        variant="glass"
                        size="sm"
                        onClick={handleDownloadJson}
                        leftIcon={<Download className="h-3.5 w-3.5" />}
                      >
                        Download
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <textarea
                      placeholder="Paste portable theme JSON here to import..."
                      value={importJsonText}
                      onChange={(e) => setImportJsonText(e.target.value)}
                      rows={3}
                      className="w-full p-2.5 rounded-xl bg-card border border-border text-[11px] font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-muted-foreground">
                        FlowPilot JSON Specification 2.0.0
                      </span>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={handleImport}
                        disabled={!importJsonText.trim()}
                        leftIcon={<Upload className="h-3.5 w-3.5" />}
                      >
                        Import Theme
                      </Button>
                    </div>
                    {importFeedback && (
                      <div
                        className={`text-xs px-3 py-1.5 rounded-lg border ${
                          importFeedback.success
                            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                            : "bg-rose-500/10 border-rose-500/30 text-rose-400"
                        }`}
                      >
                        {importFeedback.message}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Interactive Real-Time Live Preview (5 cols) */}
          <div className="lg:col-span-5 flex flex-col space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Interactive Live Preview
              </span>
              <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Live Token Binding
              </span>
            </div>

            {/* Live Preview Container Canvas */}
            <div className="flex-1 rounded-2xl glass-panel p-5 border border-border/80 flex flex-col justify-between space-y-5 bg-card/60 shadow-inner">
              {/* Preview 1: AI Core Orb & Agent Node Connection */}
              <div className="relative flex items-center justify-between p-4 rounded-xl bg-surface/70 border border-border/60 overflow-hidden">
                {/* AI Core Orb */}
                <div className="flex flex-col items-center gap-2 relative z-10">
                  <div
                    className={`h-12 w-12 rounded-full flex items-center justify-center shadow-lg border border-white/30 ${
                      themeConfig.motion !== "off" ? "ai-core-pulse" : ""
                    }`}
                    style={{
                      backgroundColor: "var(--ai-core-color)",
                      boxShadow: "0 0 25px var(--ai-core-glow)",
                    }}
                  >
                    <Sparkles className="h-6 w-6 text-black" />
                  </div>
                  <span className="text-[10px] font-mono font-bold text-foreground">
                    AI Core
                  </span>
                </div>

                {/* Animated Connection SVG */}
                <div className="flex-1 mx-3 flex items-center justify-center relative">
                  <svg className="w-full h-8" preserveAspectRatio="none">
                    <line
                      x1="0"
                      y1="16"
                      x2="100%"
                      y2="16"
                      stroke="var(--primary)"
                      strokeWidth="2"
                      strokeDasharray={themeConfig.motion !== "off" ? "4,4" : "0"}
                      className={themeConfig.motion !== "off" ? "animate-pulse" : ""}
                    />
                  </svg>
                  <span className="absolute text-[9px] font-mono bg-card px-1.5 py-0.5 rounded border border-border text-muted-foreground">
                    DAG Edge
                  </span>
                </div>

                {/* Agent Node */}
                <div className="flex flex-col items-center gap-2 relative z-10">
                  <div
                    className="h-12 w-12 rounded-xl glass-panel flex items-center justify-center border border-border shadow-md"
                    style={{
                      boxShadow:
                        themeConfig.agentGlow === "off"
                          ? "none"
                          : "0 0 15px var(--primary-glow)",
                    }}
                  >
                    <Bot className="h-6 w-6 text-primary" />
                  </div>
                  <span className="text-[10px] font-mono font-bold text-foreground">
                    LeadAgent
                  </span>
                </div>
              </div>

              {/* Preview 2: Live Metric Card */}
              <div className="p-4 rounded-xl glass-panel border border-border/80 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground font-medium">Pipeline Throughput</span>
                  <Badge variant="default" size="sm">
                    +34.8%
                  </Badge>
                </div>
                <div className="text-2xl font-bold font-mono tracking-tight text-foreground">
                  $148,200
                </div>
                <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                  <span className="h-2 w-2 rounded-full bg-primary" />
                  <span>12 Active Autonomous Agents</span>
                </div>
              </div>

              {/* Preview 3: Live Interactive Buttons */}
              <div className="grid grid-cols-2 gap-3">
                <Button variant="primary" size="md" className="w-full justify-center">
                  Execute Goal
                </Button>
                <Button variant="glass" size="md" className="w-full justify-center">
                  Inspect DAG
                </Button>
              </div>

              {/* Preview 4: Active Configuration Breakdown */}
              <div className="p-3 rounded-lg bg-surface-lowest/70 border border-border/40 text-[10px] font-mono space-y-1 text-muted-foreground">
                <div className="flex justify-between">
                  <span>Preset:</span>
                  <span className="text-foreground font-bold">{themeConfig.preset}</span>
                </div>
                <div className="flex justify-between">
                  <span>Accent:</span>
                  <span className="text-primary font-bold">{themeConfig.primaryAccent}</span>
                </div>
                <div className="flex justify-between">
                  <span>AI Core:</span>
                  <span style={{ color: "var(--ai-core-color)" }} className="font-bold">
                    {themeConfig.aiCoreColor}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Motion:</span>
                  <span className="text-foreground font-bold">{themeConfig.motion}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
