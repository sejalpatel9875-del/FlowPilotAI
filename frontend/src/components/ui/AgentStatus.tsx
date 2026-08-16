import React from "react";
import { cn } from "@/utils/cn";
import { AgentStatusType } from "@/types";
import { Badge, BadgeVariant } from "./Badge";
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
  const normalized = (status || "idle").toLowerCase();

  const getStatusConfig = () => {
    switch (normalized) {
      case "running":
      case "executing":
        return { label: "Running", icon: <Play className="h-3 w-3 fill-current" />, variant: "running" as BadgeVariant };
      case "thinking":
      case "planning":
        return { label: "Planning", icon: <Cpu className="h-3 w-3 animate-spin" />, variant: "thinking" as BadgeVariant };
      case "completed":
        return { label: "Completed", icon: <CheckCircle2 className="h-3 w-3" />, variant: "completed" as BadgeVariant };
      case "failed":
        return { label: "Failed", icon: <AlertCircle className="h-3 w-3" />, variant: "failed" as BadgeVariant };
      case "needs_approval":
      case "waiting_approval":
      case "waiting_for_approval":
        return { label: "Needs Approval", icon: <ShieldAlert className="h-3 w-3" />, variant: "warning" as BadgeVariant };
      default:
        return { label: "Idle", icon: <Clock className="h-3 w-3" />, variant: "idle" as BadgeVariant };
    }
  };

  const config = getStatusConfig();

  return (
    <Badge variant={config.variant} size={size} className={cn("font-medium tracking-tight uppercase font-mono text-[10px]", className)}>
      {showIcon && config.icon}
      <span>{config.label}</span>
    </Badge>
  );
};
