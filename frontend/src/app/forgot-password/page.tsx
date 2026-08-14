"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Zap, Mail, ArrowLeft, Send } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsLoading(true);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        throw new Error("Request failed.");
      }

      setToast({
        type: "success",
        title: "Reset Link Dispatched",
        message: "If an account exists for this email, password reset instructions have been logged.",
      });
    } catch (err: any) {
      setToast({ type: "error", title: "Error", message: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background p-4 relative overflow-hidden ambient-glow">
      <div className="w-full max-w-md space-y-6 relative z-10">
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-sky-400 text-white shadow-glow">
            <Zap className="h-6 w-6 fill-current" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Password Recovery</h1>
          <p className="text-xs text-muted-foreground">Enter your registered email address to receive reset instructions.</p>
        </div>

        {toast && (
          <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
        )}

        <Card glass className="border-indigo-500/20 shadow-2xl">
          <CardContent className="pt-6 space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                  Account Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="developer@flowpilot.ai"
                  className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isLoading}
                className="w-full mt-2 font-semibold"
                rightIcon={<Send className="h-4 w-4" />}
              >
                Send Reset Link
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          <Link href="/login" className="font-semibold text-primary hover:underline inline-flex items-center gap-1">
            <ArrowLeft className="h-3 w-3" /> Back to Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
