import React from "react";
import { cn } from "@/utils/cn";
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from "lucide-react";

export type ToastType = "success" | "warning" | "error" | "info";

export interface ToastProps {
  id?: string;
  type?: ToastType;
  title: string;
  message?: string;
  onClose?: () => void;
}

export const Toast: React.FC<ToastProps> = ({
  type = "info",
  title,
  message,
  onClose,
}) => {
  const icons = {
    success: <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />,
    warning: <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />,
    error: <XCircle className="h-5 w-5 text-rose-400 shrink-0" />,
    info: <Info className="h-5 w-5 text-sky-400 shrink-0" />,
  };

  const borders = {
    success: "border-emerald-500/20",
    warning: "border-amber-500/20",
    error: "border-rose-500/20",
    info: "border-sky-500/20",
  };

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-xl glass-panel p-4 shadow-glass max-w-sm w-full border bg-card/95 text-foreground animate-fade-in",
        borders[type]
      )}
      role="alert"
    >
      {icons[type]}
      <div className="flex-1 min-w-0">
        <h4 className="text-xs font-semibold text-foreground">{title}</h4>
        {message && <p className="text-[11px] text-muted-foreground mt-0.5">{message}</p>}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground transition-colors p-0.5 rounded-md hover:bg-muted"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
};
