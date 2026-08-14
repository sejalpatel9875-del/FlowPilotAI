import React, { useState, useRef, useEffect } from "react";
import { cn } from "@/utils/cn";

export interface DropdownItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  danger?: boolean;
  onClick?: () => void;
}

export interface DropdownProps {
  trigger: React.ReactNode;
  items: DropdownItem[];
  align?: "left" | "right";
  className?: string;
}

export const Dropdown: React.FC<DropdownProps> = ({
  trigger,
  items,
  align = "right",
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      <div onClick={() => setIsOpen(!isOpen)}>{trigger}</div>

      {isOpen && (
        <div
          className={cn(
            "absolute z-50 mt-2 w-48 rounded-xl glass-panel bg-card/95 border-border p-1.5 shadow-glass text-xs font-medium animate-fade-in",
            align === "right" ? "right-0" : "left-0",
            className
          )}
        >
          {items.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                item.onClick?.();
                setIsOpen(false);
              }}
              className={cn(
                "flex w-full items-center gap-2 px-3 py-2 text-left rounded-lg transition-colors",
                item.danger
                  ? "text-rose-400 hover:bg-rose-500/10"
                  : "text-foreground hover:bg-muted"
              )}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
