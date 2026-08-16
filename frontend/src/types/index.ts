export type AgentStatusType = 
  | "idle"
  | "thinking"
  | "running"
  | "completed"
  | "failed"
  | "needs_approval"
  | "IDLE"
  | "PLANNING"
  | "RUNNING"
  | "WAITING_APPROVAL"
  | "COMPLETED"
  | "FAILED"
  | "WARNING";

export type WorkflowStatusType =
  | "PLANNED"
  | "VALIDATING"
  | "RUNNING"
  | "WAITING_FOR_APPROVAL"
  | "APPROVED"
  | "REJECTED"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type StepStatusType =
  | "PLANNED"
  | "RUNNING"
  | "WAITING_FOR_APPROVAL"
  | "APPROVED"
  | "REJECTED"
  | "COMPLETED"
  | "FAILED"
  | "SKIPPED";

export interface AgentActivityEvent {
  id: string;
  agentId?: string;
  agentName: string;
  action: string;
  status: AgentStatusType;
  details?: string;
  timestamp: string;
  requiresApproval?: boolean;
}

export interface AgentItem {
  name: string;
  description: string;
  purpose: string;
  riskLevel: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: string;
  totalRuns: number;
  avgLatencyMs: number;
  allowedDataScopes: string[];
  allowedTools: string[];
}

export interface AgentRun {
  id: string;
  agentName: string;
  requestId?: string;
  inputSummary: string;
  status: string;
  startedAt?: string;
  completedAt?: string;
  latencyMs: number;
  outputSummary?: string;
  errorCode?: string;
}

export interface WorkflowStep {
  id: string;
  stepKey: string;
  order: number;
  agent: string;
  action: string;
  description: string;
  dependsOn: string[];
  requiresApproval: boolean;
  status: StepStatusType;
  output?: {
    agent?: string;
    action?: string;
    output?: string;
    summary?: string;
    approved_by?: string;
  };
  latencyMs: number;
  errorInfo?: string;
}

export interface WorkflowApproval {
  id: string;
  stepKey: string;
  proposedAction: string;
  status: "pending" | "approved" | "rejected" | "expired";
  createdAt?: string;
}

export interface WorkflowEvent {
  id: string;
  eventType: string;
  stepKey?: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface Workflow {
  id: string;
  title: string;
  goal: string;
  status: WorkflowStatusType;
  totalSteps: number;
  completedSteps: number;
  replanCount: number;
  errorMessage?: string;
  startedAt?: string;
  completedAt?: string;
  createdAt?: string;
  updatedAt?: string;
  steps?: WorkflowStep[];
  pendingApprovals?: WorkflowApproval[];
}

export type LeadStatus = "New" | "Qualified" | "Researching" | "Outreach Ready" | "Contacted" | "Replied" | "Meeting" | "Proposal" | "Won" | "Lost" | "Not Interested";

export interface Lead {
  id: string;
  name: string;
  company: string;
  email: string;
  website?: string;
  industry?: string;
  location?: string;
  source: string;
  serviceFit: "High" | "Medium" | "Low";
  leadScore: number;
  status: LeadStatus;
  notes?: string;
  nextAction?: string;
  verificationStatus: "Verified" | "Inferred" | "Unknown";
  value?: number;
  createdAt?: string;
}

export interface Project {
  id: string;
  title: string;
  clientName: string;
  status: "planning" | "in_progress" | "review" | "completed";
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

export interface ObservabilityOverview {
  totalRequests: number;
  avgLatencyMs: number;
  errorRate: number;
  tokensUsed: number;
  primaryProvider: string;
  primaryModel: string;
  fallbackEvents: number;
}

export interface SecurityAuditItem {
  id: string;
  action: string;
  resourceType: string;
  resourceId?: string;
  ipAddress: string;
  timestamp: string;
  details?: Record<string, any>;
}
