import React from "react";
import { cn } from "@/utils/cn";
import { AgentActivityEvent } from "@/types";
import { EmptyState } from "./EmptyState";
import { AgentStatus } from "./AgentStatus";
import { Cpu, ArrowUpRight } from "lucide-react";

export interface ActivityFeedProps {
  activities: AgentActivityEvent[];
  onApprove?: (id: string) => void;
  isLoading?: boolean;
  className?: string;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  activities,
  onApprove,
  isLoading = false,
  className,
}) => {
  if (isLoading) {
    return (
      <div className="space-y-3 p-4">
        <div className="h-14 bg-muted/40 rounded-xl animate-pulse" />
        <div className="h-14 bg-muted/40 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <EmptyState
        title="No Agent Activity Yet"
        description="Active AI workflows and background task executions will appear here in real-time."
        icon={<Cpu className="h-6 w-6 stroke-[1.5]" />}
      />
    );
  }

  return (
    <div className={cn("space-y-2.5", className)}>
      {activities.map((act) => (
        <div
          key={act.id}
          className="flex items-center justify-between p-3 rounded-xl glass-panel bg-card/70 border border-border/60 hover:bg-card-hover/90 transition-all text-xs"
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 rounded-lg bg-primary/10 text-primary shrink-0">
              <Cpu className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-foreground truncate">{act.agentName}</span>
                <AgentStatus status={act.status} size="sm" />
              </div>
              <p className="text-muted-foreground text-[11px] truncate mt-0.5">{act.action}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0 ml-3">
            <span className="text-[10px] text-muted-foreground font-mono">{act.timestamp}</span>
            {act.status === "needs_approval" && onApprove && (
              <button
                onClick={() => onApprove(act.id)}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/30 font-semibold text-[11px] transition-colors"
              >
                <span>Approve</span>
                <ArrowUpRight className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
