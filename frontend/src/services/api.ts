import { 
  CommandPromptRequest, 
  CommandPromptResponse, 
  Lead, 
  Project, 
  AgentActivityEvent,
  SystemHealthStatus 
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error ${response.status}: ${errorText || response.statusText}`);
  }

  return response.json();
}

export const apiService = {
  async checkHealth(): Promise<SystemHealthStatus> {
    try {
      return await fetchJson<SystemHealthStatus>("/health");
    } catch (err) {
      return {
        status: "error",
        database: "disconnected",
        redis: "disconnected",
        version: "1.0.0-phase1",
      };
    }
  },

  async sendCommand(request: CommandPromptRequest): Promise<CommandPromptResponse> {
    return fetchJson<CommandPromptResponse>("/command/process", {
      method: "POST",
      body: JSON.stringify(request),
    });
  },

  async getLeads(): Promise<Lead[]> {
    try {
      return await fetchJson<Lead[]>("/leads");
    } catch {
      return [];
    }
  },

  async getProjects(): Promise<Project[]> {
    try {
      return await fetchJson<Project[]>("/projects");
    } catch {
      return [];
    }
  },

  async getAgentActivities(): Promise<AgentActivityEvent[]> {
    try {
      return await fetchJson<AgentActivityEvent[]>("/agents/activity");
    } catch {
      return [];
    }
  },

  async approveAgentAction(activityId: string): Promise<{ success: boolean; message: string }> {
    return fetchJson<{ success: boolean; message: string }>(`/agents/activity/${activityId}/approve`, {
      method: "POST",
    });
  }
};
