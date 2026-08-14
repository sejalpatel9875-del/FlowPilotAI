"use client";

import React, { useEffect, useState } from "react";
import { DataTable, Column } from "@/components/ui/DataTable";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Project } from "@/types";
import { apiService } from "@/services/api";
import { Briefcase, Plus } from "lucide-react";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadProjects() {
      setIsLoading(true);
      try {
        const data = await apiService.getProjects();
        setProjects(data);
      } catch (err) {
        console.error("Error loading projects:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadProjects();
  }, []);

  const columns: Column<Project>[] = [
    { key: "title", header: "Project Title", render: (p) => <span className="font-semibold">{p.title}</span> },
    { key: "clientName", header: "Client" },
    { key: "status", header: "Status", render: (p) => <Badge variant="purple">{p.status}</Badge> },
    {
      key: "progressPercent",
      header: "Progress",
      render: (p) => (
        <div className="flex items-center gap-2">
          <div className="w-24 bg-secondary rounded-full h-2 overflow-hidden">
            <div className="bg-primary h-full rounded-full" style={{ width: `${p.progressPercent}%` }} />
          </div>
          <span className="font-mono text-xs">{p.progressPercent}%</span>
        </div>
      ),
    },
    { key: "deadline", header: "Deadline", render: (p) => <span className="font-mono text-muted-foreground">{p.deadline}</span> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Briefcase className="h-6 w-6 text-sky-400" />
            Projects & Engagements
          </h1>
          <p className="text-xs text-muted-foreground">
            Track active client deliverables, milestones, and deadlines.
          </p>
        </div>

        <Button variant="primary" size="sm" leftIcon={<Plus className="h-3.5 w-3.5" />}>
          New Project
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={projects}
        isLoading={isLoading}
        emptyTitle="No Projects Registered"
        emptyDescription="No client engagements or active software projects are currently present in database storage."
      />
    </div>
  );
}
