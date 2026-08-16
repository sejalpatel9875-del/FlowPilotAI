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

  async applyRecommendationAction(recommendationId: string, action: string): Promise<{ success: boolean }> {
    return fetchJson(`/command/recommendations/${recommendationId}/action`, {
      method: "POST",
      body: JSON.stringify({ action }),
    });
  },

  // Leads CRM
  async getLeads(): Promise<Lead[]> {
    try {
      const data = await fetchJson<any>("/leads");
      return Array.isArray(data) ? data : data.leads || [];
    } catch {
      return [];
    }
  },

  async createLead(leadData: Partial<Lead>): Promise<Lead> {
    return fetchJson<Lead>("/leads", {
      method: "POST",
      body: JSON.stringify(leadData),
    });
  },

  async executeLeadAIAction(leadId: string, actionType: "analyze" | "opportunity" | "outreach" | "recommend_next_action"): Promise<any> {
    return fetchJson(`/leads/${leadId}/ai-action`, {
      method: "POST",
      body: JSON.stringify({ actionType }),
    });
  },

  // Analytics & Observability
  async getAnalyticsOverview(): Promise<any> {
    return fetchJson("/analytics/overview");
  },

  async getAnalyticsCharts(): Promise<any> {
    return fetchJson("/analytics/charts");
  },

  // Security Center
  async getSecurityOverview(): Promise<any> {
    return fetchJson("/security/overview");
  },

  async getActiveSessions(): Promise<SessionResponse[]> {
    try {
      return await fetchJson<SessionResponse[]>("/auth/sessions");
    } catch {
      return [];
    }
  },

  async revokeSession(sessionId: string): Promise<any> {
    return fetchJson(`/auth/sessions/${sessionId}`, {
      method: "DELETE",
    });
  },

  // Projects & Workplace
  async getProjects(): Promise<Project[]> {
    try {
      const data = await fetchJson<any>("/projects");
      return Array.isArray(data) ? data : data.projects || [];
    } catch {
      return [];
    }
  },
};
