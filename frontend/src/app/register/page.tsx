"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Zap, User, Mail, Lock, UserPlus, CheckCircle2 } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  const getPasswordStrength = (pwd: string) => {
    if (!pwd) return { score: 0, label: "", color: "bg-muted" };
    if (pwd.length < 8) return { score: 1, label: "Weak (Min 8 chars)", color: "bg-rose-500" };
    const hasNum = /\d/.exec(pwd);
    const hasSpecial = /[!@#$%^&*]/.exec(pwd);
    if (hasNum && hasSpecial) return { score: 3, label: "Strong (Argon2id Encrypted)", color: "bg-emerald-500" };
    return { score: 2, label: "Medium", color: "bg-amber-500" };
  };

  const strength = getPasswordStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email || !password) return;

    setIsLoading(true);
    setToast(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fullName, email, password }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Registration failed.");
      }

      setToast({
        type: "success",
        title: "Account Created!",
        message: "Verification token generated. Redirecting to login...",
      });
      setTimeout(() => router.push("/login"), 1500);
    } catch (err: any) {
      setToast({ type: "error", title: "Registration Error", message: err.message });
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
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Create FlowPilot AI Account</h1>
          <p className="text-xs text-muted-foreground">Production Argon2id Encryption & RBAC Architecture</p>
        </div>

        {toast && (
          <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
        )}

        <Card glass className="border-indigo-500/20 shadow-2xl">
          <CardContent className="pt-6 space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                  <User className="h-3.5 w-3.5 text-muted-foreground" />
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jane Developer"
                  className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
                />
              </div>

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
                  placeholder="jane@flowpilot.ai"
                  className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5 text-muted-foreground" />
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                  className="w-full rounded-xl glass-panel bg-secondary/40 px-3.5 py-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/80"
                />
                {password && (
                  <div className="space-y-1 pt-1">
                    <div className="flex h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                      <div className={`h-full transition-all ${strength.color}`} style={{ width: `${(strength.score / 3) * 100}%` }} />
                    </div>
                    <span className="text-[10px] text-muted-foreground font-mono block">{strength.label}</span>
                  </div>
                )}
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isLoading}
                className="w-full mt-2 font-semibold"
                rightIcon={<UserPlus className="h-4 w-4" />}
              >
                Register Account
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          Already registered?{" "}
          <Link href="/login" className="font-semibold text-primary hover:underline">
            Sign in here
          </Link>
        </p>
      </div>
    </div>
  );
}
