"use client";

import React, { useState } from "react";
import { useTheme } from "@/app/providers";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { WorkspaceSwitcher } from "./WorkspaceSwitcher";
import { Dropdown } from "@/components/ui/Dropdown";
import { Button } from "@/components/ui/Button";
import { Drawer } from "@/components/ui/Drawer";
import { Sidebar } from "./Sidebar";
import {
  Search,
  Bell,
  Sun,
  Moon,
  User,
  LogOut,
  Sliders,
  Menu,
  Sparkles,
  Palette,
  Command as CommandIcon,
} from "lucide-react";

export interface TopbarProps {
  onToggleTheme?: () => void;
  isDark?: boolean;
}

export const Topbar: React.FC<TopbarProps> = ({ onToggleTheme, isDark = true }) => {
  const { openStudio, themeConfig } = useTheme();
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [hasUnreadNotifications] = useState(false);

  const userMenuItems = [
    { id: "profile", label: "Developer Profile", icon: <User className="h-3.5 w-3.5 text-muted-foreground" /> },
    {
      id: "customize",
      label: "Appearance Studio",
      icon: <Palette className="h-3.5 w-3.5 text-primary" />,
      onClick: () => openStudio(),
    },
    { id: "settings", label: "Preferences", icon: <Sliders className="h-3.5 w-3.5 text-muted-foreground" /> },
    { id: "logout", label: "Sign Out", danger: true, icon: <LogOut className="h-3.5 w-3.5 text-rose-400" /> },
  ];

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between glass-panel bg-card/80 px-4 md:px-6 border-b border-border/80 backdrop-blur-md">
        {/* Left Section: Mobile Menu Trigger & Workspace Switcher */}
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden text-muted-foreground hover:text-foreground"
            onClick={() => setIsMobileMenuOpen(true)}
            aria-label="Open navigation menu"
          >
            <Menu className="h-5 w-5" />
          </Button>

          <WorkspaceSwitcher />
        </div>

        {/* Center: Command Palette Trigger */}
        <div className="hidden sm:flex items-center flex-1 max-w-md mx-4">
          <button
            onClick={() => setIsCommandOpen(true)}
            className="flex w-full items-center justify-between rounded-xl glass-panel bg-card/40 px-3.5 py-2 text-xs text-muted-foreground hover:bg-card-hover hover:border-primary/30 border border-border/60 transition-all shadow-inner"
          >
            <div className="flex items-center gap-2">
              <Search className="h-3.5 w-3.5 text-muted-foreground" />
              <span>Search projects, leads, or ask AI...</span>
            </div>
            <div className="flex items-center gap-1 font-mono text-[10px] bg-secondary/80 px-1.5 py-0.5 rounded border border-border">
              <CommandIcon className="h-3 w-3" />
              <span>K</span>
            </div>
          </button>
        </div>

        {/* Right Section: Actions, Studio Trigger & Profile */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Flagship Appearance Studio Trigger Button */}
          <Button
            variant="glass"
            size="sm"
            onClick={openStudio}
            className="text-xs font-semibold border-primary/30 hover:border-primary text-foreground hover:shadow-md transition-all glow-primary"
            leftIcon={<span className="text-primary font-bold text-sm leading-none">◐</span>}
          >
            <span className="hidden sm:inline">Customize</span>
            <span className="text-[10px] font-mono text-primary uppercase ml-1 hidden md:inline">
              ({themeConfig.preset})
            </span>
          </Button>

          {/* Quick AI Command Center Link */}
          <Button
            variant="glass"
            size="sm"
            onClick={() => setIsCommandOpen(true)}
            className="hidden xl:inline-flex text-xs font-semibold text-purple-300 border-purple-500/30 hover:border-purple-500/50"
            leftIcon={<Sparkles className="h-3.5 w-3.5 text-purple-400" />}
          >
            AI Command
          </Button>

          {/* Quick Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleTheme}
            aria-label="Toggle theme mode"
            className="text-muted-foreground hover:text-foreground"
          >
            {isDark ? <Sun className="h-4 w-4 text-amber-300" /> : <Moon className="h-4 w-4 text-indigo-400" />}
          </Button>

          {/* Notifications */}
          <div className="relative">
            <Button
              variant="ghost"
              size="icon"
              aria-label="View notifications"
              className="text-muted-foreground hover:text-foreground"
            >
              <Bell className="h-4 w-4" />
              {hasUnreadNotifications && (
                <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-primary ring-2 ring-background" />
              )}
            </Button>
          </div>

          {/* User Profile Menu */}
          <Dropdown
            align="right"
            items={userMenuItems}
            trigger={
              <button className="flex items-center gap-2 p-1 rounded-xl glass-panel bg-card/60 hover:bg-card-hover border border-border/70 transition-all">
                <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-primary to-secondary flex items-center justify-center text-white text-xs font-bold font-mono shadow-sm">
                  FP
                </div>
              </button>
            }
          />
        </div>
      </header>

      {/* Global Command Palette Modal */}
      <CommandPalette isOpen={isCommandOpen} onClose={() => setIsCommandOpen(false)} />

      {/* Mobile Sidebar Navigation Drawer */}
      <Drawer isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} position="left" title="FlowPilot Navigation">
        <Sidebar onMobileNavigate={() => setIsMobileMenuOpen(false)} />
      </Drawer>
    </>
  );
};
