import React from "react";
import { Sparkles, Calendar, Zap } from "lucide-react";
import { Button } from "@/components/ui/Button";

export const WelcomeHeader: React.FC = () => {
  const currentDate = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="relative rounded-2xl glass-panel p-6 bg-gradient-to-r from-indigo-950/40 via-card to-purple-950/30 border border-white/10 shadow-glass overflow-hidden">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs font-mono text-indigo-400 font-medium">
            <Calendar className="h-3.5 w-3.5" />
            <span>{currentDate}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            Welcome to FlowPilot AI
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground max-w-xl leading-relaxed">
            Your AI-powered Freelancing, Growth, Productivity and Learning Operating System.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="glass"
            size="sm"
            className="text-xs border-indigo-500/30 text-indigo-300"
            leftIcon={<Zap className="h-3.5 w-3.5 text-amber-400" />}
          >
            System Active
          </Button>
        </div>
      </div>
    </div>
  );
};
