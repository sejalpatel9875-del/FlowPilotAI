"use client";

import React from "react";
import { EmptyState } from "@/components/ui/EmptyState";
import { UserCheck } from "lucide-react";

export default function ClientsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <UserCheck className="h-6 w-6 text-teal-400" />
          Client Directory
        </h1>
        <p className="text-xs text-muted-foreground">Active client accounts, contract histories, and invoices.</p>
      </div>

      <EmptyState
        title="No Client Accounts Added"
        description="Add client profiles to track contracts, billing, and communication history."
        icon={<UserCheck className="h-6 w-6 stroke-[1.5]" />}
      />
    </div>
  );
}
