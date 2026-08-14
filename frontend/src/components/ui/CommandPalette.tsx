import React, { useState, useEffect } from "react";
import { cn } from "@/utils/cn";
import { Search, Command, ArrowRight, Sparkles, Layers, UserCheck, Briefcase } from "lucide-react";
import { useRouter } from "next/navigation";

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState("");
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        isOpen ? onClose() : null;
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const defaultActions = [
    { id: "cmd", title: "Open AI Command Center", category: "Core", path: "/command-center", icon: <Sparkles className="h-4 w-4 text-purple-400" /> },
    { id: "leads", title: "View Lead Pipeline", category: "CRM", path: "/leads", icon: <UserCheck className="h-4 w-4 text-blue-400" /> },
    { id: "projects", title: "Manage Active Projects", category: "Work", path: "/projects", icon: <Briefcase className="h-4 w-4 text-emerald-400" /> },
    { id: "agents", title: "Inspect AI Agents Status", category: "Automation", path: "/agents", icon: <Layers className="h-4 w-4 text-amber-400" /> },
  ];

  const filtered = defaultActions.filter(a => 
    a.title.toLowerCase().includes(query.toLowerCase()) || 
    a.category.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (path: string) => {
    router.push(path);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-black/70 backdrop-blur-sm animate-fade-in" onClick={onClose}>
      <div
        className="w-full max-w-xl rounded-2xl glass-panel bg-card border border-white/10 shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center px-4 border-b border-border/70">
          <Search className="h-4 w-4 text-muted-foreground mr-2 shrink-0" />
          <input
            type="text"
            placeholder="Type a command or search workspace..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent py-4 text-sm text-foreground focus:outline-none placeholder:text-muted-foreground"
            autoFocus
          />
          <div className="flex items-center gap-1 text-[10px] font-mono text-muted-foreground bg-secondary/60 px-2 py-1 rounded border border-border">
            <span>ESC</span>
          </div>
        </div>

        <div className="p-2 max-h-80 overflow-y-auto divide-y divide-border/30">
          {filtered.length === 0 ? (
            <div className="py-8 text-center text-xs text-muted-foreground">
              No matching commands found.
            </div>
          ) : (
            filtered.map((item) => (
              <button
                key={item.id}
                onClick={() => handleSelect(item.path)}
                className="flex w-full items-center justify-between px-3 py-2.5 rounded-xl hover:bg-card-hover text-left text-xs transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-secondary/50 group-hover:bg-secondary transition-colors">
                    {item.icon}
                  </div>
                  <div>
                    <span className="font-semibold text-foreground block">{item.title}</span>
                    <span className="text-[10px] text-muted-foreground uppercase">{item.category}</span>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
