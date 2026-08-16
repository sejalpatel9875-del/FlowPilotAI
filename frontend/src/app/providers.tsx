"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { ThemeConfig, PresetMode, SavedCustomTheme, MotionPreset } from "@/types/theme";
import { DEFAULT_THEME_CONFIG, THEME_PRESETS, INITIAL_SAVED_THEMES } from "@/utils/themePresets";
import { applyThemeToDOM } from "@/utils/tokenGenerator";

const THEME_STORAGE_KEY = "flowpilot_adaptive_theme_config";
const SAVED_THEMES_STORAGE_KEY = "flowpilot_saved_custom_themes";

interface ThemeContextType {
  theme: "dark" | "light";
  themeConfig: ThemeConfig;
  setThemeConfig: React.Dispatch<React.SetStateAction<ThemeConfig>>;
  updateThemeProperty: <K extends keyof ThemeConfig>(key: K, value: ThemeConfig[K]) => void;
  applyPreset: (preset: PresetMode) => void;
  savedThemes: SavedCustomTheme[];
  saveCustomTheme: (name: string, config: ThemeConfig, slotId?: string) => void;
  deleteCustomTheme: (slotId: string) => void;
  exportThemeJson: (config?: ThemeConfig) => string;
  importThemeJson: (jsonString: string) => { success: boolean; message: string };
  isStudioOpen: boolean;
  openStudio: () => void;
  closeStudio: () => void;
  toggleTheme: () => void;
  resetToDefaults: () => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "dark",
  themeConfig: DEFAULT_THEME_CONFIG,
  setThemeConfig: () => {},
  updateThemeProperty: () => {},
  applyPreset: () => {},
  savedThemes: [],
  saveCustomTheme: () => {},
  deleteCustomTheme: () => {},
  exportThemeJson: () => "",
  importThemeJson: () => ({ success: false, message: "" }),
  isStudioOpen: false,
  openStudio: () => {},
  closeStudio: () => {},
  toggleTheme: () => {},
  resetToDefaults: () => {},
});

export const useTheme = () => useContext(ThemeContext);

export const Providers: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [themeConfig, setThemeConfig] = useState<ThemeConfig>(() => {
    if (typeof window !== "undefined") {
      try {
        const cached = localStorage.getItem(THEME_STORAGE_KEY);
        if (cached) {
          const parsed = JSON.parse(cached);
          return { ...DEFAULT_THEME_CONFIG, ...parsed };
        }
      } catch (e) {
        console.error("Failed to load theme config from localStorage:", e);
      }
    }
    return DEFAULT_THEME_CONFIG;
  });

  const [savedThemes, setSavedThemes] = useState<SavedCustomTheme[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const cached = localStorage.getItem(SAVED_THEMES_STORAGE_KEY);
        if (cached) {
          return JSON.parse(cached);
        }
      } catch (e) {
        console.error("Failed to load saved themes from localStorage:", e);
      }
    }
    return INITIAL_SAVED_THEMES;
  });

  const [isStudioOpen, setIsStudioOpen] = useState(false);

  // Time & System adaptive check for 'auto' preset
  const resolveAutoConfig = useCallback((baseConfig: ThemeConfig): ThemeConfig => {
    if (baseConfig.preset !== "auto") return baseConfig;

    const hour = new Date().getHours();
    const isNightTime = hour >= 19 || hour < 7;
    const prefersDark = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)").matches : true;

    if (baseConfig.timeAwareAuto) {
      if (isNightTime || prefersDark) {
        return {
          ...baseConfig,
          background: "dark",
          primaryAccent: "blue",
          aiCoreColor: "cyan",
        };
      } else {
        return {
          ...baseConfig,
          background: "light",
          primaryAccent: "blue",
          aiCoreColor: "cyan",
        };
      }
    }
    return baseConfig;
  }, []);

  // Real-time live DOM update whenever themeConfig changes
  useEffect(() => {
    const effectiveConfig = resolveAutoConfig(themeConfig);
    applyThemeToDOM(effectiveConfig);

    try {
      localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(themeConfig));
    } catch (e) {
      // Storage quota exceeded or disabled
    }
  }, [themeConfig, resolveAutoConfig]);

  // Sync saved themes to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(SAVED_THEMES_STORAGE_KEY, JSON.stringify(savedThemes));
    } catch (e) {
      // Storage quota
    }
  }, [savedThemes]);

  // Cross-tab synchronization
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === THEME_STORAGE_KEY && e.newValue) {
        try {
          const synced = JSON.parse(e.newValue);
          setThemeConfig(synced);
        } catch (err) {}
      }
      if (e.key === SAVED_THEMES_STORAGE_KEY && e.newValue) {
        try {
          setSavedThemes(JSON.parse(e.newValue));
        } catch (err) {}
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const updateThemeProperty = useCallback(<K extends keyof ThemeConfig>(key: K, value: ThemeConfig[K]) => {
    setThemeConfig((prev) => ({
      ...prev,
      preset: key === "preset" ? (value as PresetMode) : "custom",
      [key]: value,
    }));
  }, []);

  const applyPreset = useCallback((preset: PresetMode) => {
    if (THEME_PRESETS[preset]) {
      setThemeConfig({ ...THEME_PRESETS[preset].config, preset });
    }
  }, []);

  const saveCustomTheme = useCallback((name: string, config: ThemeConfig, slotId?: string) => {
    const now = Date.now();
    setSavedThemes((prev) => {
      if (slotId) {
        return prev.map((t) => (t.id === slotId ? { ...t, name, config, updatedAt: now } : t));
      }
      const newTheme: SavedCustomTheme = {
        id: `slot-${Date.now()}`,
        name: name || `Custom Theme ${prev.length + 1}`,
        config: { ...config, preset: "custom" },
        createdAt: now,
        updatedAt: now,
      };
      return [...prev, newTheme];
    });
  }, []);

  const deleteCustomTheme = useCallback((slotId: string) => {
    setSavedThemes((prev) => prev.filter((t) => t.id !== slotId));
  }, []);

  const exportThemeJson = useCallback((config?: ThemeConfig): string => {
    const target = config || themeConfig;
    const payload = {
      app: "FlowPilot AI",
      version: "2.0.0",
      type: "AdaptiveAppearanceTheme",
      exportedAt: new Date().toISOString(),
      theme: target,
    };
    return JSON.stringify(payload, null, 2);
  }, [themeConfig]);

  const importThemeJson = useCallback((jsonString: string): { success: boolean; message: string } => {
    try {
      const parsed = JSON.parse(jsonString);
      const incomingTheme = parsed.theme || parsed;

      if (!incomingTheme.background || !incomingTheme.primaryAccent) {
        return { success: false, message: "Invalid theme format. Missing core color tokens." };
      }

      const validated: ThemeConfig = {
        ...DEFAULT_THEME_CONFIG,
        ...incomingTheme,
        preset: "custom",
      };

      setThemeConfig(validated);
      return { success: true, message: "Theme imported successfully!" };
    } catch (e: any) {
      return { success: false, message: `Failed to parse theme JSON: ${e.message}` };
    }
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeConfig((prev) => {
      const nextBg = prev.background === "light" || prev.background === "warm" ? "dark" : "light";
      const nextPreset = nextBg === "light" ? "arctic" : "obsidian";
      return {
        ...THEME_PRESETS[nextPreset].config,
        preset: nextPreset,
        background: nextBg,
      };
    });
  }, []);

  const resetToDefaults = useCallback(() => {
    setThemeConfig(DEFAULT_THEME_CONFIG);
  }, []);

  const isLightOrWarm = themeConfig.background === "light" || themeConfig.background === "warm";
  const theme: "dark" | "light" = isLightOrWarm ? "light" : "dark";

  return (
    <ThemeContext.Provider
      value={{
        theme,
        themeConfig,
        setThemeConfig,
        updateThemeProperty,
        applyPreset,
        savedThemes,
        saveCustomTheme,
        deleteCustomTheme,
        exportThemeJson,
        importThemeJson,
        isStudioOpen,
        openStudio: () => setIsStudioOpen(true),
        closeStudio: () => setIsStudioOpen(false),
        toggleTheme,
        resetToDefaults,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};
