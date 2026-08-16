import { ThemeConfig, AccentColor, AICoreColor, BackgroundMode } from "@/types/theme";

export const ACCENT_COLOR_MAP: Record<AccentColor, { hex: string; rgb: string; glow: string; name: string }> = {
  blue: { hex: "#2E7BFF", rgb: "46, 123, 255", glow: "rgba(46, 123, 255, 0.35)", name: "Electric Blue" },
  violet: { hex: "#8B5CF6", rgb: "139, 92, 246", glow: "rgba(139, 92, 246, 0.35)", name: "Cosmic Violet" },
  teal: { hex: "#14B8A6", rgb: "20, 184, 166", glow: "rgba(20, 184, 166, 0.35)", name: "Neon Teal" },
  cyan: { hex: "#06B6D4", rgb: "6, 182, 212", glow: "rgba(6, 182, 212, 0.35)", name: "Cyber Cyan" },
  rose: { hex: "#F43F5E", rgb: "244, 63, 94", glow: "rgba(244, 63, 94, 0.35)", name: "Vibrant Rose" },
  emerald: { hex: "#10B981", rgb: "16, 185, 129", glow: "rgba(16, 185, 129, 0.35)", name: "Emerald Intelligence" },
  amber: { hex: "#F59E0B", rgb: "245, 158, 11", glow: "rgba(245, 158, 11, 0.35)", name: "Warm Amber" },
  custom: { hex: "#2E7BFF", rgb: "46, 123, 255", glow: "rgba(46, 123, 255, 0.35)", name: "Custom Hex" },
};

export const AI_CORE_COLOR_MAP: Record<AICoreColor, { hex: string; rgb: string; glow: string; name: string }> = {
  cyan: { hex: "#00E5FF", rgb: "0, 229, 255", glow: "rgba(0, 229, 255, 0.45)", name: "Singularity Cyan" },
  blue: { hex: "#38BDF8", rgb: "56, 189, 248", glow: "rgba(56, 189, 248, 0.45)", name: "Plasma Blue" },
  violet: { hex: "#A855F7", rgb: "168, 85, 247", glow: "rgba(168, 85, 247, 0.45)", name: "Neural Violet" },
  teal: { hex: "#14B8A6", rgb: "20, 184, 166", glow: "rgba(20, 184, 166, 0.45)", name: "Ethereal Teal" },
  emerald: { hex: "#34D399", rgb: "52, 211, 153", glow: "rgba(52, 211, 153, 0.45)", name: "Matrix Emerald" },
  rose: { hex: "#FB7185", rgb: "251, 113, 133", glow: "rgba(251, 113, 133, 0.45)", name: "Pulse Rose" },
  amber: { hex: "#FBBF24", rgb: "251, 191, 36", glow: "rgba(251, 191, 36, 0.45)", name: "Fusion Amber" },
  custom: { hex: "#00E5FF", rgb: "0, 229, 255", glow: "rgba(0, 229, 255, 0.45)", name: "Custom Core" },
};

function hexToRgb(hex: string): string {
  const cleanHex = hex.replace("#", "");
  if (cleanHex.length === 3) {
    const r = parseInt(cleanHex[0] + cleanHex[0], 16);
    const g = parseInt(cleanHex[1] + cleanHex[1], 16);
    const b = parseInt(cleanHex[2] + cleanHex[2], 16);
    return `${r}, ${g}, ${b}`;
  }
  if (cleanHex.length === 6) {
    const r = parseInt(cleanHex.substring(0, 2), 16);
    const g = parseInt(cleanHex.substring(2, 4), 16);
    const b = parseInt(cleanHex.substring(4, 6), 16);
    return `${r}, ${g}, ${b}`;
  }
  return "46, 123, 255";
}

export function generateCssVariables(config: ThemeConfig): Record<string, string> {
  const isLight = config.background === "light";
  const isWarm = config.background === "warm";

  // 1. Accent Color Resolution
  let accentHex = config.customAccentHex || ACCENT_COLOR_MAP[config.primaryAccent]?.hex || "#2E7BFF";
  let accentRgb = hexToRgb(accentHex);
  let accentGlow = `rgba(${accentRgb}, 0.35)`;

  // 2. AI Core Color Resolution
  let aiCoreHex = config.customAICoreHex || AI_CORE_COLOR_MAP[config.aiCoreColor]?.hex || "#00E5FF";
  let aiCoreRgb = hexToRgb(aiCoreHex);
  let aiCoreGlow = `rgba(${aiCoreRgb}, 0.50)`;

  // 3. Background & Surface Color Architecture
  let bg = "#05070B";
  let fg = "#E1E2E9";
  let surface = "#111318";
  let surfaceLow = "#191C20";
  let surfaceContainer = "#1D2024";
  let surfaceHigh = "#272A2F";
  let card = "rgba(17, 19, 24, 0.75)";
  let cardHover = "rgba(29, 32, 36, 0.85)";
  let muted = "#191C20";
  let mutedFg = "#94A3B8";

  if (isLight) {
    bg = "#F8FAFC";
    fg = "#0F172A";
    surface = "#FFFFFF";
    surfaceLow = "#F1F5F9";
    surfaceContainer = "#E2E8F0";
    surfaceHigh = "#CBD5E1";
    card = "rgba(255, 255, 255, 0.85)";
    cardHover = "rgba(241, 245, 249, 0.95)";
    muted = "#F1F5F9";
    mutedFg = "#64748B";
  } else if (isWarm) {
    bg = "#FDFBF7";
    fg = "#292524";
    surface = "#F7F4EB";
    surfaceLow = "#EFEADF";
    surfaceContainer = "#E5DFD1";
    surfaceHigh = "#D6CFC0";
    card = "rgba(247, 244, 235, 0.90)";
    cardHover = "rgba(239, 234, 223, 0.95)";
    muted = "#EFEADF";
    mutedFg = "#78716C";
  } else if (config.customBackgroundHex) {
    bg = config.customBackgroundHex;
    const bgRgb = hexToRgb(bg);
    surface = `rgba(${bgRgb}, 0.92)`;
    surfaceLow = `rgba(${bgRgb}, 0.80)`;
    surfaceContainer = `rgba(${bgRgb}, 0.70)`;
    card = `rgba(${bgRgb}, 0.75)`;
    cardHover = `rgba(${bgRgb}, 0.85)`;
  }

  // 4. Glass Intensity
  let glassBlur = "16px";
  let glassBgOpacity = "0.70";
  if (config.glassIntensity === "minimal") {
    glassBlur = "8px";
    glassBgOpacity = isLight || isWarm ? "0.95" : "0.85";
  } else if (config.glassIntensity === "strong") {
    glassBlur = "28px";
    glassBgOpacity = isLight || isWarm ? "0.65" : "0.55";
  }

  // 5. Border Intensity
  let borderAlpha = "0.08";
  let borderHoverAlpha = "0.18";
  if (isLight || isWarm) {
    borderAlpha = config.borderIntensity === "subtle" ? "0.06" : config.borderIntensity === "strong" ? "0.20" : "0.12";
    borderHoverAlpha = "0.25";
  } else {
    borderAlpha = config.borderIntensity === "subtle" ? "0.05" : config.borderIntensity === "strong" ? "0.18" : "0.10";
    borderHoverAlpha = config.borderIntensity === "strong" ? "0.30" : "0.20";
  }

  // 6. Motion Speed
  let motionDuration = "0.2s";
  let pulseSpeed = "2.5s";
  if (config.motion === "off") {
    motionDuration = "0.001s";
    pulseSpeed = "0s";
  } else if (config.motion === "subtle") {
    motionDuration = "0.3s";
    pulseSpeed = "4s";
  } else if (config.motion === "immersive") {
    motionDuration = "0.18s";
    pulseSpeed = "1.8s";
  }

  // 7. Density Scaling
  let densityPadding = config.density === "compact" ? "0.5rem" : "0.875rem";
  let densityGap = config.density === "compact" ? "0.5rem" : "0.75rem";

  return {
    "--background": bg,
    "--foreground": fg,
    "--surface": surface,
    "--surface-lowest": isLight || isWarm ? "#FFFFFF" : "#080A0E",
    "--surface-low": surfaceLow,
    "--surface-container": surfaceContainer,
    "--surface-high": surfaceHigh,
    "--card": card,
    "--card-foreground": fg,
    "--card-hover": cardHover,
    "--primary": accentHex,
    "--primary-rgb": accentRgb,
    "--primary-foreground": isLight || isWarm ? "#FFFFFF" : "#FFFFFF",
    "--primary-glow": accentGlow,
    "--secondary": isLight || isWarm ? "#6366F1" : "#8B5CF6",
    "--secondary-glow": isLight || isWarm ? "rgba(99, 102, 241, 0.3)" : "rgba(139, 92, 246, 0.3)",
    "--ai-core-color": aiCoreHex,
    "--ai-core-rgb": aiCoreRgb,
    "--ai-core-glow": aiCoreGlow,
    "--ai-core-pulse-speed": pulseSpeed,
    "--muted": muted,
    "--muted-foreground": mutedFg,
    "--border": isLight || isWarm ? `rgba(0, 0, 0, ${borderAlpha})` : `rgba(255, 255, 255, ${borderAlpha})`,
    "--border-hover": isLight || isWarm ? `rgba(0, 0, 0, ${borderHoverAlpha})` : `rgba(255, 255, 255, ${borderHoverAlpha})`,
    "--glass-blur": glassBlur,
    "--glass-bg": isLight ? `rgba(255, 255, 255, ${glassBgOpacity})` : isWarm ? `rgba(247, 244, 235, ${glassBgOpacity})` : `rgba(17, 19, 24, ${glassBgOpacity})`,
    "--glass-border": isLight || isWarm ? `rgba(0, 0, 0, ${borderAlpha})` : `rgba(255, 255, 255, ${borderAlpha})`,
    "--motion-duration": motionDuration,
    "--density-padding": densityPadding,
    "--density-gap": densityGap,
  };
}

export function applyThemeToDOM(config: ThemeConfig) {
  if (typeof document === "undefined") return;

  const root = document.documentElement;
  const isLightOrWarm = config.background === "light" || config.background === "warm";

  // Set data attributes
  root.setAttribute("data-theme", config.preset);
  root.setAttribute("data-density", config.density);
  root.setAttribute("data-motion", config.motion);
  root.setAttribute("data-bg-effect", config.backgroundEffect);
  root.setAttribute("data-is-dark", isLightOrWarm ? "false" : "true");

  if (isLightOrWarm) {
    root.classList.add("light");
    root.classList.remove("dark");
  } else {
    root.classList.add("dark");
    root.classList.remove("light");
  }

  // Inject CSS Variables directly into root style
  const vars = generateCssVariables(config);
  for (const [key, value] of Object.entries(vars)) {
    root.style.setProperty(key, value);
  }
}
