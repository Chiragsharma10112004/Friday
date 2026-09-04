import { fetchApi } from "./client";
import {
  SystemStatus,
  DetailedHealth,
  ReadinessHealth,
  DiagnosticsHealth,
  ChatRequest,
  ChatResponse,
  WorkspaceMap,
  SymbolDefinition,
  TestRunReport,
  CodeEditRequest,
  CodeEditResponse,
  DiagnosticReport,
  RemediationProposal,
  RemediationResult,
  SelfHealingAuditRecord,
  TodayActionQueueResponse,
  ActionItemResponse,
  DashboardIntelligenceResponse,
  ApplicationHealthListResponse,
  ApplicationHealthItem,
  DailyBriefingResponse,
  WeeklyBriefingResponse,
  WorkflowResponse,
  WorkflowListResponse,
  WorkflowQueueResponse,
  WorkflowDashboardResponse,
  WorkflowStep,
  WorkflowActionLog,
  WorkflowApproval,
  ApplicationResponse,
  ApplicationListResponse,
  PipelineSummaryResponse,
  FollowUpCategoryResponse,
  ApplicationTimelineEventResponse,
  InterviewResponse,
  DiscoveredJob,
  OpportunityListResponse,
  JobSearchResponse,
  OutcomeFeedbackResponse,
  AssetVersionResponse,
  FieldIssueResponse,
  AnalyticsSummaryResponse,
  ConversionFunnelResponse,
  PlatformPerformanceResponse,
  FeedbackSignalResponse,
  FeedbackRankResponse,
  MemoryResponse,
  ChatHistoryItem,
  UserProfileResponse,
} from "@/types";

export const systemApi = {
  getStatus: () => fetchApi<SystemStatus>("/status"),
  getHealth: () => fetchApi<{ status: string; timestamp: string }>("/health"),
  getDetailedHealth: () => fetchApi<DetailedHealth>("/health/detailed"),
  getReadiness: () => fetchApi<ReadinessHealth>("/health/readiness"),
  getDiagnostics: () => fetchApi<DiagnosticsHealth>("/health/diagnostics"),
};

export const chatApi = {
  sendMessage: (message: string) =>
    fetchApi<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
};

export const developerApi = {
  getWorkspace: (root: string = ".") =>
    fetchApi<WorkspaceMap>(`/developer/workspace?root=${encodeURIComponent(root)}`),
  lookupSymbols: (name: string, root: string = ".") =>
    fetchApi<SymbolDefinition[]>(
      `/developer/symbols?name=${encodeURIComponent(name)}&root=${encodeURIComponent(root)}`
    ),
  runTests: (target: string = "tests.run_all_phase_tests", timeout: number = 60) =>
    fetchApi<TestRunReport>("/developer/run-tests", {
      method: "POST",
      body: JSON.stringify({ target, timeout }),
    }),
  editCode: (req: CodeEditRequest) =>
    fetchApi<CodeEditResponse>("/developer/edit", {
      method: "POST",
      body: JSON.stringify(req),
    }),
};

export const selfHealingApi = {
  diagnose: (errorMessage: string, tracebackText: string, errorType?: string) =>
    fetchApi<DiagnosticReport>("/self-healing/diagnose", {
      method: "POST",
      body: JSON.stringify({
        error_message: errorMessage,
        traceback_text: tracebackText,
        error_type: errorType,
      }),
    }),
  plan: (report: DiagnosticReport) =>
    fetchApi<RemediationProposal>("/self-healing/plan", {
      method: "POST",
      body: JSON.stringify(report),
    }),
  executeProposal: (proposalId: string, approved: boolean = true) =>
    fetchApi<RemediationResult>(`/self-healing/execute/${proposalId}`, {
      method: "POST",
      body: JSON.stringify({ approved }),
    }),
  autoHeal: (params: {
    errorMessage: string;
    tracebackText: string;
    errorType?: string;
    approved?: boolean;
    proposedCodeOverride?: string;
    customValidationCmd?: string;
  }) =>
    fetchApi<RemediationResult>("/self-healing/auto-heal", {
      method: "POST",
      body: JSON.stringify({
        error_message: params.errorMessage,
        traceback_text: params.tracebackText,
        error_type: params.errorType,
        approved: params.approved ?? true,
        proposed_code_override: params.proposedCodeOverride,
        custom_validation_cmd: params.customValidationCmd,
      }),
    }),
  getHistory: () => fetchApi<SelfHealingAuditRecord[]>("/self-healing/history"),
};

export const careerIntelligenceApi = {
  getToday: () => fetchApi<TodayActionQueueResponse>("/career-intelligence/today"),
  getNextActions: (params?: { priority?: string; recommendation_type?: string }) => {
    const query = new URLSearchParams();
    if (params?.priority) query.append("priority", params.priority);
    if (params?.recommendation_type) query.append("recommendation_type", params.recommendation_type);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchApi<ActionItemResponse[]>(`/career-intelligence/next-actions${qs}`);
  },
  getDashboard: () => fetchApi<DashboardIntelligenceResponse>("/career-intelligence/dashboard"),
  getApplicationHealth: () =>
    fetchApi<ApplicationHealthListResponse>("/career-intelligence/application-health"),
  getSingleApplicationHealth: (id: number) =>
    fetchApi<ApplicationHealthItem>(`/career-intelligence/application-health/${id}`),
  getDailyBriefing: () => fetchApi<DailyBriefingResponse>("/career-intelligence/daily-briefing"),
  getWeeklyBriefing: () => fetchApi<WeeklyBriefingResponse>("/career-intelligence/weekly-briefing"),
  dismissRecommendation: (id: number) =>
    fetchApi<ActionItemResponse>(`/career-intelligence/recommendations/${id}/dismiss`, {
      method: "POST",
    }),
  completeRecommendation: (id: number) =>
    fetchApi<ActionItemResponse>(`/career-intelligence/recommendations/${id}/complete`, {
      method: "POST",
    }),
  refreshRecommendations: () =>
    fetchApi<{ recalculated_count: number }>("/career-intelligence/recommendations/refresh", {
      method: "POST",
    }),
};

export const workflowApi = {
  getQueue: () => fetchApi<WorkflowQueueResponse>("/workflow/queue"),
  getDashboard: () => fetchApi<WorkflowDashboardResponse>("/workflow/dashboard"),
  listWorkflows: (params?: { status?: string; company?: string; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append("status", params.status);
    if (params?.company) query.append("company", params.company);
    if (params?.limit) query.append("limit", params.limit.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchApi<WorkflowListResponse>(`/workflow${qs}`);
  },
  getWorkflow: (id: number) => fetchApi<WorkflowResponse>(`/workflow/${id}`),
  createWorkflow: (data: {
    company: string;
    role: string;
    source_url?: string;
    source_platform?: string;
    priority?: string;
    match_score?: number;
  }) =>
    fetchApi<WorkflowResponse>("/workflow", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  createFromOpportunity: (opportunityId: number, priority?: string) =>
    fetchApi<WorkflowResponse>(`/workflow/from-opportunity/${opportunityId}`, {
      method: "POST",
      body: JSON.stringify({ priority }),
    }),
  startWorkflow: (id: number) =>
    fetchApi<WorkflowResponse>(`/workflow/${id}/start`, { method: "POST" }),
  approveCheckpoint: (id: number, req?: { approval_type?: string; reason?: string }) =>
    fetchApi<WorkflowResponse>(`/workflow/${id}/approve`, {
      method: "POST",
      body: JSON.stringify(req || {}),
    }),
  rejectCheckpoint: (id: number, reason?: string) =>
    fetchApi<WorkflowResponse>(`/workflow/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),
  pauseWorkflow: (id: number) =>
    fetchApi<WorkflowResponse>(`/workflow/${id}/pause`, { method: "POST" }),
  resumeWorkflow: (id: number) =>
    fetchApi<WorkflowResponse>(`/workflow/${id}/resume`, { method: "POST" }),
  retryWorkflow: (id: number) =>
    fetchApi<WorkflowResponse>(`/workflow/${id}/retry`, { method: "POST" }),
  cancelWorkflow: (id: number) =>
    fetchApi<WorkflowResponse>(`/workflow/${id}/cancel`, { method: "POST" }),
  getSteps: (id: number) =>
    fetchApi<{ workflow_id: number; total_steps: number; steps: WorkflowStep[] }>(
      `/workflow/${id}/steps`
    ),
  getActions: (id: number) =>
    fetchApi<{ workflow_id: number; total_logs: number; action_logs: WorkflowActionLog[] }>(
      `/workflow/${id}/actions`
    ),
  getApprovals: (id: number) =>
    fetchApi<{ workflow_id: number; total_approvals: number; approvals: WorkflowApproval[] }>(
      `/workflow/${id}/approvals`
    ),
  confirmManualSubmission: (id: number, notes?: string) =>
    fetchApi<WorkflowResponse>(`/workflow/${id}/confirm-manual-submission`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    }),
};

export const applicationsApi = {
  listApplications: (params?: {
    status?: string;
    company?: string;
    role?: string;
    priority?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append("status", params.status);
    if (params?.company) query.append("company", params.company);
    if (params?.role) query.append("role", params.role);
    if (params?.priority) query.append("priority", params.priority);
    if (params?.page) query.append("page", params.page.toString());
    if (params?.page_size) query.append("page_size", params.page_size.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchApi<ApplicationListResponse>(`/applications${qs}`);
  },
  createApplication: (data: {
    company: string;
    role: string;
    source_url?: string;
    source_platform?: string;
    status?: string;
    match_score?: number;
  }) =>
    fetchApi<ApplicationResponse>("/applications", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getSummary: () => fetchApi<PipelineSummaryResponse>("/applications/summary"),
  getFollowUps: () => fetchApi<FollowUpCategoryResponse>("/applications/follow-ups"),
  getApplication: (id: number) => fetchApi<ApplicationResponse>(`/applications/${id}`),
  updateApplication: (id: number, data: Partial<ApplicationResponse>) =>
    fetchApi<ApplicationResponse>(`/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  transitionStatus: (id: number, newStatus: string, reason?: string) =>
    fetchApi<ApplicationResponse>(`/applications/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ new_status: newStatus, transition_reason: reason }),
    }),
  markApplied: (id: number, notes?: string) =>
    fetchApi<ApplicationResponse>(`/applications/${id}/mark-applied`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    }),
  getTimeline: (id: number) =>
    fetchApi<ApplicationTimelineEventResponse[]>(`/applications/${id}/timeline`),
  addNote: (id: number, noteText: string) =>
    fetchApi<ApplicationResponse>(`/applications/${id}/notes`, {
      method: "POST",
      body: JSON.stringify({ note_text: noteText }),
    }),
  listInterviews: (id: number) =>
    fetchApi<InterviewResponse[]>(`/applications/${id}/interviews`),
  createInterview: (
    id: number,
    data: {
      round_number: number;
      stage_name: string;
      interview_type?: string;
      scheduled_at?: string;
      notes?: string;
    }
  ) =>
    fetchApi<InterviewResponse>(`/applications/${id}/interviews`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export const jobsApi = {
  searchJobs: (query: { role: string; location?: string; provider?: string; limit?: number }) =>
    fetchApi<JobSearchResponse>("/job-discovery/search", {
      method: "POST",
      body: JSON.stringify(query),
    }),
  listOpportunities: (params?: {
    company?: string;
    title?: string;
    provider?: string;
    is_remote?: boolean;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.company) query.append("company", params.company);
    if (params?.title) query.append("title", params.title);
    if (params?.provider) query.append("provider", params.provider);
    if (params?.is_remote !== undefined) query.append("is_remote", String(params.is_remote));
    if (params?.page) query.append("page", params.page.toString());
    if (params?.page_size) query.append("page_size", params.page_size.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchApi<OpportunityListResponse>(`/opportunities${qs}`);
  },
  getOpportunity: (id: number) => fetchApi<DiscoveredJob>(`/opportunities/${id}`),
};

export const feedbackApi = {
  listOutcomes: (params?: { company?: string; outcome_type?: string }) => {
    const query = new URLSearchParams();
    if (params?.company) query.append("company", params.company);
    if (params?.outcome_type) query.append("outcome_type", params.outcome_type);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchApi<OutcomeFeedbackResponse[]>(`/feedback/outcomes${qs}`);
  },
  recordOutcome: (data: {
    application_id: number;
    outcome_type: string;
    feedback_stage: string;
    reasons_cited?: string[];
    skills_passed?: string[];
    skills_failed?: string[];
    difficulty?: string;
    experience?: string;
    salary_offered?: number;
    notes?: string;
  }) =>
    fetchApi<OutcomeFeedbackResponse>("/feedback/outcomes", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getAssetVersions: (applicationId: number) =>
    fetchApi<AssetVersionResponse[]>(`/feedback/assets/application/${applicationId}`),
  listFieldIssues: (params?: { resolved?: boolean; platform?: string }) => {
    const query = new URLSearchParams();
    if (params?.resolved !== undefined) query.append("resolved", String(params.resolved));
    if (params?.platform) query.append("platform", params.platform);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchApi<FieldIssueResponse[]>(`/feedback/field-issues${qs}`);
  },
  resolveFieldIssue: (issueId: number) =>
    fetchApi<FieldIssueResponse>(`/feedback/field-issues/${issueId}/resolve`, {
      method: "POST",
    }),
  getAnalyticsSummary: () => fetchApi<AnalyticsSummaryResponse>("/feedback/analytics/summary"),
  getFunnel: () => fetchApi<ConversionFunnelResponse>("/feedback/analytics/funnel"),
  getPlatformMetrics: () =>
    fetchApi<PlatformPerformanceResponse[]>("/feedback/analytics/platforms"),
  listSignals: () => fetchApi<FeedbackSignalResponse[]>("/feedback/signals"),
  rankOpportunity: (data: {
    company: string;
    role: string;
    match_score: number;
    missing_skills?: string[];
  }) =>
    fetchApi<FeedbackRankResponse>("/feedback/rank", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export const memoryApi = {
  getAllMemory: () => fetchApi<MemoryResponse>("/memory"),
  saveMemory: (key: string, value: string) =>
    fetchApi<{ key: string; value: string }>("/memory", {
      method: "POST",
      body: JSON.stringify({ key, value }),
    }),
  deleteMemory: (key: string) =>
    fetchApi<{ success: boolean; message: string }>(`/memory/${encodeURIComponent(key)}`, {
      method: "DELETE",
    }),
  getChatHistory: (limit: number = 20) =>
    fetchApi<ChatHistoryItem[]>(`/memory/history?limit=${limit}`),
};

export const profileApi = {
  getProfile: () => fetchApi<UserProfileResponse>("/profile"),
  updateProfile: (data: Partial<UserProfileResponse>) =>
    fetchApi<UserProfileResponse>("/profile", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};
