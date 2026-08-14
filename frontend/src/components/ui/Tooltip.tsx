import React, { useState } from "react";
import { cn } from "@/utils/cn";

export interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: "top" | "bottom" | "left" | "right";
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = "top",
}) => {
  const [visible, setVisible] = useState(false);

  const positionStyles = {
    top: "-top-8 left-1/2 -translate-x-1/2",
    bottom: "-bottom-8 left-1/2 -translate-x-1/2",
    left: "-left-2 top-1/2 -translate-y-1/2 -translate-x-full",
    right: "-right-2 top-1/2 -translate-y-1/2 translate-x-full",
  };

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div
          role="tooltip"
          className={cn(
            "absolute z-50 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-[11px] font-medium text-slate-100 shadow-md border border-slate-800 pointer-events-none transition-opacity duration-150",
            positionStyles[position]
          )}
        >
          {content}
        </div>
      )}
    </div>
  );
};
