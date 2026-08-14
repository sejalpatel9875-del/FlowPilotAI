import React from "react";
import { cn } from "@/utils/cn";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 
    | "default" 
    | "secondary" 
    | "outline" 
    | "success" 
    | "warning" 
    | "danger" 
    | "info" 
    | "purple"
    | "idle"
    | "thinking"
    | "running"
    | "completed"
    | "failed"
    | "needs_approval";
  size?: "sm" | "md";
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "default",
  size = "md",
  children,
  ...props
}) => {
  const baseStyles = "inline-flex items-center font-medium rounded-full border transition-colors";
  
  const sizeStyles = {
    sm: "px-2 py-0.5 text-[10px] gap-1",
    md: "px-2.5 py-0.5 text-xs gap-1.5",
  };

  const variantStyles = {
    default: "bg-primary/10 text-primary border-primary/20",
    secondary: "bg-secondary text-secondary-foreground border-border",
    outline: "bg-transparent text-foreground border-border",
    success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    danger: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    info: "bg-sky-500/10 text-sky-400 border-sky-500/20",
    purple: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    
    // Agent status specific badges
    idle: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    thinking: "bg-purple-500/15 text-purple-300 border-purple-500/30 animate-pulse",
    running: "bg-blue-500/15 text-blue-400 border-blue-500/30",
    completed: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    failed: "bg-rose-500/15 text-rose-400 border-rose-500/30",
    needs_approval: "bg-amber-500/15 text-amber-400 border-amber-500/30 ring-1 ring-amber-500/20",
  };

  return (
    <span
      className={cn(baseStyles, sizeStyles[size], variantStyles[variant], className)}
      {...props}
    >
      {children}
    </span>
  );
};
