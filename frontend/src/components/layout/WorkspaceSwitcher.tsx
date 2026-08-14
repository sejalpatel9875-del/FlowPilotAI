"use client";

import React, { useState } from "react";
import { Dropdown } from "@/components/ui/Dropdown";
import { Building2, Check, Plus, ChevronDown } from "lucide-react";

export const WorkspaceSwitcher: React.FC = () => {
  const [currentWorkspace, setCurrentWorkspace] = useState("Freelance Studio HQ");

  const workspaces = [
    { id: "ws1", label: "Freelance Studio HQ" },
    { id: "ws2", label: "Agency Operations" },
    { id: "ws3", label: "Personal Incubator" },
  ];

  const dropdownItems = [
    ...workspaces.map((ws) => ({
      id: ws.id,
      label: ws.label,
      icon: currentWorkspace === ws.label ? <Check className="h-3.5 w-3.5 text-primary" /> : <Building2 className="h-3.5 w-3.5 text-muted-foreground" />,
      onClick: () => setCurrentWorkspace(ws.label),
    })),
    {
      id: "add_ws",
      label: "Create Workspace...",
      icon: <Plus className="h-3.5 w-3.5 text-indigo-400" />,
      onClick: () => {},
    },
  ];

  return (
    <Dropdown
      align="left"
      items={dropdownItems}
      trigger={
        <button className="flex items-center gap-2 px-3 py-1.5 rounded-xl glass-panel bg-card/60 hover:bg-card-hover border border-border/70 text-xs font-medium text-foreground transition-all">
          <Building2 className="h-3.5 w-3.5 text-indigo-400" />
          <span className="truncate max-w-[120px] font-semibold">{currentWorkspace}</span>
          <ChevronDown className="h-3 w-3 text-muted-foreground" />
        </button>
      }
    />
  );
};
