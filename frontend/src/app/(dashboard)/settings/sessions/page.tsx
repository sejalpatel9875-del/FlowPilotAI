"use client";

import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Toast, ToastType } from "@/components/ui/Toast";
import { SessionResponse } from "@/types";
import { Laptop, Smartphone, ShieldAlert, LogOut, RefreshCw, Clock } from "lucide-react";

export default function SessionsPage() {
  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  const fetchSessions = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/sessions", {
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to fetch active sessions.");
      const data = await res.json();
      setSessions(data);
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleRevokeSession = async (sessionId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/auth/sessions/${sessionId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to revoke session.");
      setToast({ type: "success", title: "Session Revoked", message: `Session ${sessionId} terminated.` });
      await fetchSessions();
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    }
  };

  const handleLogoutAll = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/logout-all", {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to revoke all sessions.");
      setToast({ type: "success", title: "All Sessions Revoked", message: "Redirecting to login..." });
      setTimeout(() => (window.location.href = "/login"), 1000);
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Laptop className="h-6 w-6 text-indigo-400" />
            Active Session & Device Manager
          </h1>
          <p className="text-xs text-muted-foreground">
            Manage authenticated device sessions, token expiration, and remote session revocations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchSessions} leftIcon={<RefreshCw className="h-3.5 w-3.5" />}>
            Refresh
          </Button>
          <Button variant="danger" size="sm" onClick={handleLogoutAll} leftIcon={<ShieldAlert className="h-3.5 w-3.5" />}>
            Revoke All Other Sessions
          </Button>
        </div>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      <Card glass>
        <CardHeader>
          <CardTitle className="text-base">Authenticated Sessions</CardTitle>
          <CardDescription>HTTP-Only secure cookie sessions currently active in database</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-6 text-center text-xs text-muted-foreground">Loading active sessions...</div>
          ) : sessions.length === 0 ? (
            <div className="py-6 text-center text-xs text-muted-foreground">No active sessions found.</div>
          ) : (
            <div className="space-y-3">
              {sessions.map((sess) => (
                <div
                  key={sess.id}
                  className="p-4 rounded-xl glass-panel bg-card/70 border border-border/60 flex items-center justify-between gap-4 text-xs"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 shrink-0 border border-indigo-500/20">
                      <Laptop className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-foreground truncate">{sess.deviceInfo}</span>
                        {sess.isCurrentSession && <Badge variant="completed">Current Session</Badge>}
                      </div>
                      <div className="flex items-center gap-3 text-[11px] text-muted-foreground font-mono mt-1">
                        <span>IP: {sess.ipAddress}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Expires: {sess.expiresAt}
                        </span>
                      </div>
                    </div>
                  </div>

                  {!sess.isCurrentSession && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRevokeSession(sess.id)}
                      className="text-rose-400 hover:bg-rose-500/10 hover:text-rose-300"
                    >
                      Revoke
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
