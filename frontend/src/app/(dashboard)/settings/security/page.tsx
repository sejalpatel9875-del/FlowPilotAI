"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Toast, ToastType } from "@/components/ui/Toast";
import {
  Shield,
  KeyRound,
  Smartphone,
  Lock,
  History,
  CheckCircle2,
  AlertTriangle,
  ArrowRight
} from "lucide-react";

export default function SecuritySettingsPage() {
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Shield className="h-6 w-6 text-indigo-400" />
            Security & Governance Settings
          </h1>
          <p className="text-xs text-muted-foreground">
            Manage Argon2id password encryption, active sessions, RBAC permissions, and security audit logs.
          </p>
        </div>

        <Link href="/settings/sessions">
          <Button variant="glass" size="sm" rightIcon={<ArrowRight className="h-3.5 w-3.5" />}>
            Manage Active Sessions
          </Button>
        </Link>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Security Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Card 1: Password & Cryptography Engine */}
        <Card glass>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Lock className="h-4 w-4 text-purple-400" />
              Password Cryptography Engine
            </CardTitle>
            <CardDescription>Zero-knowledge password hashing configuration</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-card/80 border border-border/60 flex items-center justify-between">
              <div>
                <span className="font-semibold text-foreground block">Hashing Algorithm</span>
                <span className="text-[11px] text-muted-foreground">Argon2id (Time=3, Mem=64MB, Parallelism=4)</span>
              </div>
              <Badge variant="completed">Active</Badge>
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full justify-center"
              onClick={() => setToast({ type: "info", title: "Password Change", message: "Dispatched reset authorization link to your email." })}
              leftIcon={<KeyRound className="h-3.5 w-3.5" />}
            >
              Update Password
            </Button>
          </CardContent>
        </Card>

        {/* Card 2: Multi-Factor Authentication */}
        <Card glass>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Smartphone className="h-4 w-4 text-emerald-400" />
              Two-Factor Authentication (2FA)
            </CardTitle>
            <CardDescription>Hardware key or TOTP authenticator app protection</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-card/80 border border-border/60 flex items-center justify-between">
              <div>
                <span className="font-semibold text-foreground block">TOTP Authenticator</span>
                <span className="text-[11px] text-muted-foreground">Enforce 2FA on login</span>
              </div>
              <Badge variant="warning">Optional</Badge>
            </div>

            <Button
              variant="secondary"
              size="sm"
              className="w-full justify-center"
              onClick={() => setToast({ type: "info", title: "2FA Setup", message: "Authenticator app setup initiated." })}
            >
              Configure 2FA App
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Security Audit Log */}
      <Card glass>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <History className="h-4 w-4 text-sky-400" />
            Security Audit Trail
          </CardTitle>
          <CardDescription>Recent account security events & device authentications</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-xs">
            <div className="p-3 rounded-xl bg-card/60 border border-border/50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                <div>
                  <span className="font-semibold text-foreground block">Argon2id Authentication Success</span>
                  <span className="text-[11px] text-muted-foreground font-mono">127.0.0.1 • Web Dashboard</span>
                </div>
              </div>
              <span className="text-[10px] text-muted-foreground font-mono">Just now</span>
            </div>

            <div className="p-3 rounded-xl bg-card/60 border border-border/50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="h-4 w-4 text-purple-400 shrink-0" />
                <div>
                  <span className="font-semibold text-foreground block">Role Authorization Verified</span>
                  <span className="text-[11px] text-muted-foreground font-mono">RBAC Role: USER</span>
                </div>
              </div>
              <span className="text-[10px] text-muted-foreground font-mono">Active</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
