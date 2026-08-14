export type AgentStatusType = 
  | "idle"
  | "thinking"
  | "running"
  | "completed"
  | "failed"
  | "needs_approval";

export interface AgentActivityEvent {
  id: string;
  agentId: string;
  agentName: string;
  action: string;
  status: AgentStatusType;
  details?: string;
  timestamp: string;
  requiresApproval?: boolean;
}

export type LeadStatus = "new" | "contacted" | "qualified" | "proposal" | "won" | "lost";

export interface Lead {
  id: string;
  name: string;
  company: string;
  email: string;
  value: number;
  score: number;
  status: LeadStatus;
  source: string;
  lastContactedAt?: string;
  nextFollowUpAt?: string;
}

export type ProjectStatus = "planning" | "in_progress" | "review" | "completed";

export interface Project {
  id: string;
  title: string;
  clientName: string;
  status: ProjectStatus;
  deadline: string;
  progressPercent: number;
  hourlyRate?: number;
  budgetAllocated?: number;
}

export interface TaskItem {
  id: string;
  title: string;
  projectId?: string;
  dueDate?: string;
  completed: boolean;
  priority: "low" | "medium" | "high" | "urgent";
}

export interface CommandPromptRequest {
  query: string;
  context?: Record<string, any>;
}

export interface CommandPromptResponse {
  id: string;
  query: string;
  suggestedAction: string;
  reasoning: string[];
  recommendedSteps: {
    title: string;
    description: string;
    agentToAssign?: string;
  }[];
  timestamp: string;
}

export interface MetricData {
  title: string;
  value: string | number;
  changePercent?: number;
  changePeriod?: string;
  trend?: "up" | "down" | "neutral";
  subtitle?: string;
}

export interface SystemHealthStatus {
  status: "ok" | "degraded" | "error";
  database: "connected" | "disconnected";
  redis: "connected" | "disconnected";
  version: string;
}

export interface UserResponse {
  id: string;
  email: string;
  fullName: string;
  isActive: boolean;
  isVerified: boolean;
  roles: string[];
}

export interface SessionResponse {
  id: string;
  deviceInfo: string;
  ipAddress: string;
  isActive: boolean;
  expiresAt: string;
  createdAt: string;
  isCurrentSession: boolean;
}
