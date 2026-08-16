/**
 * FlowPilot AI — Adaptive Appearance Studio Type Definitions
 */

export type PresetMode =
  | "auto"
  | "obsidian"
  | "aurora"
  | "arctic"
  | "paper"
  | "midnight"
  | "focus"
  | "custom";

export type BackgroundMode = "dark" | "light" | "warm" | "custom";

export type AccentColor =
  | "blue"
  | "violet"
  | "teal"
  | "cyan"
  | "rose"
  | "emerald"
  | "amber"
  | "custom";

export type AICoreColor =
  | "cyan"
  | "blue"
  | "violet"
  | "teal"
  | "emerald"
  | "rose"
  | "amber"
  | "custom";

export type AgentGlowMode = "global" | "individual" | "monochrome" | "off";

export type GlassIntensity = "minimal" | "balanced" | "strong";

export type BorderIntensity = "subtle" | "standard" | "strong";

export type MotionPreset = "off" | "subtle" | "cinematic" | "immersive";

export type BackgroundEffect = "none" | "grid" | "particles" | "aurora" | "ambient_glow";

export type Density = "comfortable" | "compact";

export interface ThemeConfig {
  preset: PresetMode;
  background: BackgroundMode;
  customBackgroundHex?: string;
  primaryAccent: AccentColor;
  customAccentHex?: string;
  aiCoreColor: AICoreColor;
  customAICoreHex?: string;
  agentGlow: AgentGlowMode;
  glassIntensity: GlassIntensity;
  borderIntensity: BorderIntensity;
  motion: MotionPreset;
  backgroundEffect: BackgroundEffect;
  density: Density;
  timeAwareAuto: boolean;
}

export interface SavedCustomTheme {
  id: string;
  name: string;
  config: ThemeConfig;
  createdAt: number;
  updatedAt: number;
}

export interface ThemeRecommendation {
  id: string;
  title: string;
  description: string;
  badge: string;
  actionLabel: string;
  suggestedPreset: PresetMode;
  suggestedMotion?: MotionPreset;
  applied: boolean;
}
