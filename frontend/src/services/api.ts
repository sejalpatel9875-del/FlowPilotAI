import {
  Workflow,
  WorkflowEvent,
  AgentItem,
  AgentRun,
  Lead,
  Project,
  SystemHealthStatus,
  UserResponse,
  SessionResponse,
  SecurityAuditItem,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(`API Error ${response.status}: ${errorDetail || "Request failed"}`);
  }

  return response.json();
}

export const apiService = {
  // System Health
  async checkHealth(): Promise<SystemHealthStatus> {
    try {
      return await fetchJson<SystemHealthStatus>("/health");
    } catch {
      return {
        status: "error",
        database: "disconnected",
        redis: "disconnected",
        version: "1.0.0-phase6",
      };
    }
  },

  // Multi-Agent Workflows
  async createWorkflow(goal: string): Promise<Workflow> {
    return fetchJson<Workflow>("/workflows", {
      method: "POST",
      body: JSON.stringify({ goal }),
    });
  },

  async getWorkflow(workflowId: string): Promise<Workflow> {
    return fetchJson<Workflow>(`/workflows/${workflowId}`);
  },

  async listWorkflows(status?: string): Promise<{ workflows: Workflow[] }> {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return fetchJson<{ workflows: Workflow[] }>(`/workflows${query}`);
  },

  async approveWorkflowAction(workflowId: string, approvalId: string, reason?: string): Promise<{ workflowId: string; status: string; message: string }> {
    return fetchJson<{ workflowId: string; status: string; message: string }>(`/workflows/${workflowId}/approve`, {
      method: "POST",
      body: JSON.stringify({ approvalId, decision: "approved", reason }),
    });
  },

  async rejectWorkflowAction(workflowId: string, approvalId: string, reason?: string): Promise<{ workflowId: string; status: string; message: string }> {
    return fetchJson<{ workflowId: string; status: string; message: string }>(`/workflows/${workflowId}/reject`, {
      method: "POST",
      body: JSON.stringify({ approvalId, decision: "rejected", reason }),
    });
  },

  async cancelWorkflow(workflowId: string): Promise<{ workflowId: string; status: string; message: string }> {
    return fetchJson<{ workflowId: string; status: string; message: string }>(`/workflows/${workflowId}/cancel`, {
      method: "POST",
    });
  },

  async getWorkflowEvents(workflowId: string): Promise<{ workflowId: string; events: WorkflowEvent[] }> {
    return fetchJson<{ workflowId: string; events: WorkflowEvent[] }>(`/workflows/${workflowId}/events`);
  },

  streamWorkflow(
    workflowId: string,
    onMessage: (event: { event: string; data: any }) => void,
    onError?: (err: any) => void
  ): () => void {
    const url = `${API_BASE_URL}/workflows/${workflowId}/stream`;
    const eventSource = new EventSource(url, { withCredentials: true });

    eventSource.addEventListener("connected", (e: MessageEvent) => {
      try {
        onMessage({ event: "connected", data: JSON.parse(e.data) });
      } catch {
        onMessage({ event: "connected", data: e.data });
      }
    });

    eventSource.addEventListener("state_change", (e: MessageEvent) => {
      try {
        onMessage({ event: "state_change", data: JSON.parse(e.data) });
      } catch {
        onMessage({ event: "state_change", data: e.data });
      }
    });

    eventSource.addEventListener("terminal", (e: MessageEvent) => {
      try {
        onMessage({ event: "terminal", data: JSON.parse(e.data) });
      } catch {
        onMessage({ event: "terminal", data: e.data });
      }
      eventSource.close();
    });

    eventSource.onerror = (err) => {
      if (onError) onError(err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  },

  // Specialized Agents Registry & Execution
  async getAgentsDashboard(): Promise<{ agents: AgentItem[]; totalRuns: number; activeAgentsCount: number }> {
    return fetchJson<{ agents: AgentItem[]; totalRuns: number; activeAgentsCount: number }>("/agents/dashboard");
  },

  async getAgentRuns(): Promise<{ runs: AgentRun[] }> {
    return fetchJson<{ runs: AgentRun[] }>("/agents/runs");
  },

  async executeAgentTask(prompt: string, targetAgentName?: string): Promise<{
    requestId: string;
    agentsExecuted: string[];
    totalLatencyMs: number;
    finalResponse: string;
    runs: any[];
  }> {
    return fetchJson("/agents/execute", {
      method: "POST",
      body: JSON.stringify({ prompt, target_agent: targetAgentName }),
    });
  },

  async runAgent(agentName: string, prompt: string): Promise<any> {
    const res = await this.executeAgentTask(prompt, agentName);
    return {
      output: res.finalResponse,
      latencyMs: res.totalLatencyMs,
      requestId: res.requestId,
      runs: res.runs,
    };
  },

  // Command Center
  async whatShouldIDoNext(): Promise<{
    topRecommendations: any[];
    recommendationId: string;
    aiAnalysisSummary: string;
  }> {
    return fetchJson("/command/what-should-i-do-next", {
      method: "POST",
    });
  },

  // Analytics
  async getAnalyticsOverview(): Promise<any> {
    return fetchJson("/analytics/overview");
  },

  // Leads
  async getLeads(): Promise<Lead[]> {
    const data = await fetchJson<{ leads: Lead[] }>("/leads");
    return data.leads || [];
  },

  async createLead(leadData: Partial<Lead>): Promise<Lead> {
    return fetchJson<Lead>("/leads", {
      method: "POST",
      body: JSON.stringify(leadData),
    });
  },

  // Projects
  async getProjects(): Promise<Project[]> {
    const data = await fetchJson<{ projects: Project[] }>("/projects");
    return data.projects || [];
  },

  // Security & Audit
  async getSecurityAudit(): Promise<SecurityAuditItem[]> {
    const data = await fetchJson<{ events: SecurityAuditItem[] }>("/security/events");
    return data.events || [];
  },
};
