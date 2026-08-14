import React, { useEffect } from "react";
import { cn } from "@/utils/cn";
import { X } from "lucide-react";
import { Button } from "./Button";

export interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  position?: "left" | "right";
  children: React.ReactNode;
  className?: string;
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  position = "right",
  children,
  className,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const positionStyles = {
    left: "left-0 inset-y-0 translate-x-0 border-r",
    right: "right-0 inset-y-0 translate-x-0 border-l",
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm transition-opacity"
      onClick={onClose}
    >
      <div
        className={cn(
          "fixed z-50 w-full max-w-md bg-card glass-panel p-6 shadow-2xl transition-transform duration-300 border-border flex flex-col h-full",
          positionStyles[position],
          className
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between pb-4 border-b border-border/50">
          <h3 className="text-base font-semibold text-foreground">{title || "Menu"}</h3>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close drawer">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto py-4">{children}</div>
      </div>
    </div>
  );
};
