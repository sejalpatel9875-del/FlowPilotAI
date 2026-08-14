"use client";

import React from "react";
import { EmptyState } from "@/components/ui/EmptyState";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <Settings className="h-6 w-6 text-slate-400" />
          Workspace Settings
        </h1>
        <p className="text-xs text-muted-foreground">General settings, user profile, billing details, and API configuration.</p>
      </div>

      <EmptyState
        title="Workspace Configuration Active"
        description="Phase 1 default system configuration is loaded."
        icon={<Settings className="h-6 w-6 stroke-[1.5]" />}
      />
    </div>
  );
}
