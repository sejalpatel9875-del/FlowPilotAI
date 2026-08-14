"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Zap, CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";

function VerifyEmailForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function verify() {
      if (!token) {
        setStatus("error");
        setMessage("No verification token specified in URL query.");
        return;
      }

      try {
        const res = await fetch("http://localhost:8000/api/v1/auth/verify-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Verification failed.");
        }

        setStatus("success");
        setMessage("Your email address has been verified successfully.");
      } catch (err: any) {
        setStatus("error");
        setMessage(err.message);
      }
    }
    verify();
  }, [token]);

  return (
    <div className="w-full max-w-md space-y-6 relative z-10 text-center">
      <div className="flex flex-col items-center space-y-2">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-sky-400 text-white shadow-glow">
          <Zap className="h-6 w-6 fill-current" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Email Verification</h1>
      </div>

      <Card glass className="border-indigo-500/20 shadow-2xl p-6">
        <CardContent className="space-y-4 pt-4">
          {status === "verifying" && (
            <div className="space-y-2">
              <div className="animate-spin h-8 w-8 mx-auto text-primary border-2 border-primary border-t-transparent rounded-full" />
              <p className="text-xs text-muted-foreground">Verifying email token signature...</p>
            </div>
          )}

          {status === "success" && (
            <div className="space-y-3">
              <CheckCircle2 className="h-10 w-10 text-emerald-400 mx-auto" />
              <h3 className="text-base font-semibold text-foreground">Verification Complete</h3>
              <p className="text-xs text-muted-foreground">{message}</p>
              <Button variant="primary" size="md" className="w-full mt-2" rightIcon={<ArrowRight className="h-4 w-4" />}>
                <Link href="/login">Proceed to Login</Link>
              </Button>
            </div>
          )}

          {status === "error" && (
            <div className="space-y-3">
              <AlertCircle className="h-10 w-10 text-rose-400 mx-auto" />
              <h3 className="text-base font-semibold text-rose-200">Verification Failed</h3>
              <p className="text-xs text-rose-300/80">{message}</p>
              <Button variant="outline" size="md" className="w-full mt-2">
                <Link href="/login">Return to Login</Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background p-4 relative overflow-hidden ambient-glow">
      <Suspense fallback={<div className="text-xs text-muted-foreground">Verifying email...</div>}>
        <VerifyEmailForm />
      </Suspense>
    </div>
  );
}
