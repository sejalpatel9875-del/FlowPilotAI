import React from "react";
import { cn } from "@/utils/cn";
import { AgentStatusType } from "@/types";
import { Badge } from "./Badge";
import { Play, CheckCircle2, AlertCircle, Clock, Cpu, ShieldAlert } from "lucide-react";

export interface AgentStatusProps {
  status: AgentStatusType;
  showIcon?: boolean;
  size?: "sm" | "md";
  className?: string;
}

export const AgentStatus: React.FC<AgentStatusProps> = ({
  status,
  showIcon = true,
  size = "md",
  className,
}) => {
  const statusConfig: Record<AgentStatusType, { label: string; icon: React.ReactNode }> = {
    idle: { label: "Idle", icon: <Clock className="h-3 w-3" /> },
    thinking: { label: "Thinking", icon: <Cpu className="h-3 w-3 animate-spin" /> },
    running: { label: "Running", icon: <Play className="h-3 w-3 fill-current" /> },
    completed: { label: "Completed", icon: <CheckCircle2 className="h-3 w-3" /> },
    failed: { label: "Failed", icon: <AlertCircle className="h-3 w-3" /> },
    needs_approval: { label: "Needs Approval", icon: <ShieldAlert className="h-3 w-3" /> },
  };

  const config = statusConfig[status] || statusConfig.idle;

  return (
    <Badge variant={status} size={size} className={cn("font-medium tracking-tight uppercase", className)}>
      {showIcon && config.icon}
      <span>{config.label}</span>
    </Badge>
  );
};
