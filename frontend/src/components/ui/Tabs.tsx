import React, { useState } from "react";
import { cn } from "@/utils/cn";

export interface TabItem {
  id: string;
  label: string;
  badge?: string | number;
  icon?: React.ReactNode;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab?: string;
  onChange?: (tabId: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab: controlledActiveTab,
  onChange,
  className,
}) => {
  const [internalActiveTab, setInternalActiveTab] = useState(tabs[0]?.id || "");
  const activeTab = controlledActiveTab !== undefined ? controlledActiveTab : internalActiveTab;

  const handleSelect = (id: string) => {
    setInternalActiveTab(id);
    onChange?.(id);
  };

  return (
    <div className={cn("flex items-center gap-1 border-b border-border/80 pb-px overflow-x-auto no-scrollbar", className)}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => handleSelect(tab.id)}
            className={cn(
              "flex items-center gap-2 px-3.5 py-2 text-xs font-medium transition-all relative border-b-2 -mb-px whitespace-nowrap focus-visible:outline-none",
              isActive
                ? "border-primary text-primary font-semibold"
                : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
            )}
          >
            {tab.icon}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={cn(
                  "px-1.5 py-0.5 text-[10px] rounded-full font-mono font-medium",
                  isActive ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"
                )}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
