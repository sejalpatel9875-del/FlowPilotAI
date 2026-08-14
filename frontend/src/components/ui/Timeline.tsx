import React from "react";
import { cn } from "@/utils/cn";
import { AgentActivityEvent } from "@/types";
import { AgentStatus } from "./AgentStatus";
import { Clock } from "lucide-react";

export interface TimelineProps {
  events: AgentActivityEvent[];
  onApprove?: (id: string) => void;
  className?: string;
}

export const Timeline: React.FC<TimelineProps> = ({ events, onApprove, className }) => {
  if (!events || events.length === 0) {
    return (
      <div className="py-6 text-center text-xs text-muted-foreground">
        No timeline events recorded yet.
      </div>
    );
  }

  return (
    <div className={cn("relative space-y-4 pl-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-border/60", className)}>
      {events.map((evt) => (
        <div key={evt.id} className="relative flex items-start gap-3 text-xs">
          <div className="absolute -left-4 top-1.5 h-2.5 w-2.5 rounded-full bg-primary ring-4 ring-background" />
          
          <div className="flex-1 rounded-xl glass-panel p-3 bg-card/60 border border-border/50 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-foreground">{evt.agentName}</span>
              <AgentStatus status={evt.status} size="sm" />
            </div>
            
            <p className="text-muted-foreground text-[11px] font-mono">{evt.action}</p>
            
            {evt.details && (
              <div className="bg-secondary/40 p-2 rounded text-[11px] font-mono text-slate-300 border border-border/40">
                {evt.details}
              </div>
            )}

            <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {evt.timestamp}
              </span>

              {evt.status === "needs_approval" && onApprove && (
                <button
                  onClick={() => onApprove(evt.id)}
                  className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/30 font-medium text-[10px]"
                >
                  Approve Action
                </button>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
