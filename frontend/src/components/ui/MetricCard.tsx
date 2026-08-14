import React from "react";
import { cn } from "@/utils/cn";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card } from "./Card";

export interface MetricCardProps {
  title: string;
  value: string | number;
  changePercent?: number;
  changePeriod?: string;
  trend?: "up" | "down" | "neutral";
  icon?: React.ReactNode;
  subtitle?: string;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  changePercent,
  changePeriod = "vs last month",
  trend,
  icon,
  subtitle,
  className,
}) => {
  return (
    <Card hoverEffect glass className={cn("relative overflow-hidden group", className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
          {title}
        </span>
        {icon && (
          <div className="p-2 rounded-lg bg-secondary/80 text-muted-foreground group-hover:text-primary transition-colors">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-2xl font-bold tracking-tight text-foreground font-mono">
          {value}
        </span>
      </div>

      {(changePercent !== undefined || subtitle) && (
        <div className="mt-2 flex items-center gap-1.5 text-[11px] text-muted-foreground">
          {changePercent !== undefined && (
            <span
              className={cn(
                "inline-flex items-center font-medium font-mono px-1.5 py-0.5 rounded",
                trend === "up" && "bg-emerald-500/10 text-emerald-400",
                trend === "down" && "bg-rose-500/10 text-rose-400",
                trend === "neutral" && "bg-slate-500/10 text-slate-400"
              )}
            >
              {trend === "up" && <TrendingUp className="mr-1 h-3 w-3" />}
              {trend === "down" && <TrendingDown className="mr-1 h-3 w-3" />}
              {trend === "neutral" && <Minus className="mr-1 h-3 w-3" />}
              {changePercent > 0 ? `+${changePercent}%` : `${changePercent}%`}
            </span>
          )}
          <span>{changePeriod || subtitle}</span>
        </div>
      )}
    </Card>
  );
};
