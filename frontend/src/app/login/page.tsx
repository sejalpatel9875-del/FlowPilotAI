"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Zap, Mail, Lock, LogIn, ArrowRight, ShieldCheck } from "lucide-react";
import { apiService } from "@/services/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setIsLoading(true);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Authentication failed.");
      }

      setToast({ type: "success", title: "Welcome back!", message: "Redirecting to Command Center..." });
      setTimeout(() => router.push("/command-center"), 1000);
    } catch (err: any) {
      setToast({ type: "error", title: "Login Failed", message: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleOAuth = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/oauth/google/url");
      const data = await res.json();
      setToast({ type: "info", title: "Google OAuth Initialized", message: `Redirecting to ${data.provider}...` });
      window.location.href = data.url;
    } catch (err) {
      setToast({ type: "error", title: "OAuth Error", message: "Failed to fetch OAuth redirect URI." });
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background p-4 relative overflow-hidden ambient-glow">
      <div className="w-full max-w-md space-y-6 relative z-10">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-sky-400 text-white shadow-glow">
            <Zap className="h-6 w-6 fill-current" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Sign in to FlowPilot AI</h1>
          <p className="text-xs text-muted-foreground">AI-Powered Freelancing & Productivity Operating System</p>
        </div>

        {/* Toast Alert Banner */}
        {toast && (
          <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
        )}

        {/* Login Form Card */}
        <Card glass className="border-indigo-500/20 shadow-2xl">
          <CardContent className="pt-6 space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                  Email Address
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

              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                    <Lock className="h-3.5 w-3.5 text-muted-foreground" />
                    Password
                  </label>
                  <Link href="/forgot-password" className="text-[11px] text-indigo-400 hover:underline">
                    Forgot password?
                  </Link>
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isLoading}
                className="w-full mt-2 font-semibold"
                rightIcon={<LogIn className="h-4 w-4" />}
              >
                Sign In
              </Button>
            </form>

            <div className="relative my-4 flex items-center justify-center">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-border/60" /></div>
              <span className="relative bg-card px-2 text-[10px] uppercase text-muted-foreground">Or continue with</span>
            </div>

            {/* Google OAuth Button */}
            <Button
              variant="outline"
              size="md"
              onClick={handleGoogleOAuth}
              className="w-full text-xs font-medium justify-center gap-2"
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              Google OAuth2
            </Button>
          </CardContent>
        </Card>

        {/* Footer link */}
        <p className="text-center text-xs text-muted-foreground">
          Don't have an account?{" "}
          <Link href="/register" className="font-semibold text-primary hover:underline">
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
}
