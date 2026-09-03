// ==============================================================================
// FRIDAY TypeScript Type Definitions (Aligned with FastAPI Backend Models)
// ==============================================================================

export interface SystemStatus {
  assistant: string;
  version: string;
  environment: string;
  status: string;
}

export interface DetailedHealth {
  status: string;
  timestamp: string;
  application: string;
  version: string;
  environment: string;
}

export interface ReadinessHealth {
  status: "ready" | "degraded";
  database: string;
  timestamp: string;
  application: string;
  version: string;
}

export interface DiagnosticsHealth {
  status: string;
  timestamp: string;
  total_self_healing_events: number;
  recent_recovery_events: SelfHealingAuditRecord[];
}

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  reply: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  toolsUsed?: string[];
  status?: "pending" | "streaming" | "complete" | "error";
}

export interface SymbolDefinition {
  name: string;
  symbol_type: "function" | "class" | "import";
  file: string;
  line: number;
  docstring?: string | null;
  parameters: string[];
}

export interface FileInspection {
  path: string;
  name: string;
  size_bytes: number;
  lines_count: number;
  symbols_count: number;
  functions: string[];
  classes: string[];
  imports: string[];
}

export interface WorkspaceMap {
  root_path: string;
  total_files: number;
  total_lines: number;
  files: FileInspection[];
  symbol_index: Record<string, string[]>;
}

export interface TestCaseResult {
  name: string;
  status: "PASSED" | "FAILED" | "ERROR" | "SKIPPED";
  duration_sec: number;
  error_message?: string | null;
  stack_trace?: string | null;
}

export interface TestRunReport {
  total_run: number;
  passed: number;
  failed: number;
  errors: number;
  duration_sec: number;
  success: boolean;
  test_cases: TestCaseResult[];
  raw_output: string;
}

export interface CodeEditRequest {
  function_name: string;
  instruction: string;
  preview?: boolean;
}

export interface CodeEditResponse {
  success: boolean;
  diff?: string;
  original?: string;
  updated?: string;
  error?: string;
}

export type FailureCategory =
  | "SYNTAX_ERROR"
  | "IMPORT_ERROR"
  | "TEST_FAILURE"
  | "RUNTIME_EXCEPTION"
  | "CONFIGURATION_ERROR"
  | "DEPENDENCY_MISSING"
  | "TIMEOUT"
  | "UNKNOWN";

export type RemediationStrategy =
  | "AST_FUNCTION_REPLACE"
  | "IMPORT_INSERTION"
  | "SYNTAX_REPAIR"
  | "CONFIG_CORRECTION"
  | "DEPENDENCY_INSTALL"
  | "MANUAL_ESCALATION";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type RecoveryStatus =
  | "PENDING_APPROVAL"
  | "IN_PROGRESS"
  | "RECOVERED"
  | "VALIDATION_FAILED"
  | "ROLLED_BACK"
  | "ESCALATED";

export interface DiagnosticReport {
  category: FailureCategory;
  error_type: string;
  error_message: string;
  target_file?: string | null;
  target_line?: number | null;
  target_symbol?: string | null;
  stack_trace_snippet?: string | null;
  context_code?: string | null;
  failing_tests: string[];
  timestamp?: string;
}

export interface RemediationProposal {
  proposal_id: string;
  category: FailureCategory;
  strategy: RemediationStrategy;
  risk_level: RiskLevel;
  description: string;
  target_file: string;
  target_symbol?: string | null;
  proposed_code?: string | null;
  diff_preview?: string | null;
  requires_approval: boolean;
  validation_command?: string | null;
  created_at?: string;
}

export interface RemediationResult {
  proposal_id: string;
  status: RecoveryStatus;
  strategy_applied: RemediationStrategy;
  target_file: string;
  diff_applied?: string | null;
  validation_passed: boolean;
  validation_output?: string | null;
  attempts: number;
  error?: string | null;
  timestamp?: string;
}

export interface SelfHealingAuditRecord {
  id: string;
  timestamp: string;
  category: FailureCategory;
  target_file: string;
  strategy: RemediationStrategy;
  status: RecoveryStatus;
  validation_passed: boolean;
  summary: string;
}

export interface ActionItemResponse {
  id: number;
  recommendation_type: string;
  title: string;
  description: string;
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  status: "ACTIVE" | "COMPLETED" | "DISMISSED" | "EXPIRED";
  application_id?: number | null;
  opportunity_id?: number | null;
  suggested_action: string;
  reason: string;
  created_at: string;
}

export interface TodayActionQueueResponse {
  total_actions: number;
  critical_count: number;
  high_count: number;
  actions: ActionItemResponse[];
  briefing_headline: string;
}

export interface ApplicationHealthItem {
  application_id: number;
  company: string;
  role: string;
  status: string;
  health_score: number;
  health_status: "EXCELLENT" | "GOOD" | "ATTENTION_NEEDED" | "STALE" | "CRITICAL";
  days_in_current_status: number;
  is_stale: boolean;
  is_overdue: boolean;
  issues: string[];
  recommendations: string[];
}

export interface ApplicationHealthListResponse {
  total_tracked: number;
  healthy_count: number;
  attention_needed_count: number;
  stale_count: number;
  critical_count: number;
  items: ApplicationHealthItem[];
}

export interface DashboardIntelligenceResponse {
  pipeline_health: ApplicationHealthListResponse;
  today_action_queue: TodayActionQueueResponse;
  briefing_snippet: string;
}

export interface DailyBriefingResponse {
  generated_at: string;
  headline: string;
  key_metrics: Record<string, any>;
  top_priorities: ActionItemResponse[];
  market_insights: string[];
}

export interface WeeklyBriefingResponse {
  week_start: string;
  week_end: string;
  summary: string;
  applications_sent: number;
  interviews_held: number;
  conversion_rate: number;
}

export interface WorkflowStep {
  id: number;
  step_name: string;
  step_type: string;
  status: string;
  order_index: number;
  input_payload?: Record<string, any> | null;
  output_payload?: Record<string, any> | null;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface WorkflowApproval {
  id: number;
  workflow_id: number;
  approval_type: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  checkpoint_data?: Record<string, any> | null;
  reason?: string | null;
  requested_at: string;
  resolved_at?: string | null;
}

export interface WorkflowActionLog {
  id: number;
  workflow_id: number;
  action_name: string;
  description: string;
  status: string;
  created_at: string;
}

export interface WorkflowResponse {
  id: number;
  company: string;
  role: string;
  source_url?: string | null;
  source_platform: string;
  priority: string;
  status: string;
  opportunity_id?: number | null;
  application_id?: number | null;
  match_score?: number | null;
  user_action_required: boolean;
  current_step?: string | null;
  steps: WorkflowStep[];
  pending_approvals: WorkflowApproval[];
  created_at: string;
  updated_at?: string | null;
}

export interface WorkflowListResponse {
  total: number;
  items: WorkflowResponse[];
}

export interface WorkflowQueueResponse {
  actionable_count: number;
  awaiting_approval_count: number;
  in_progress_count: number;
  completed_count: number;
  items: WorkflowResponse[];
}

export interface WorkflowDashboardResponse {
  total_workflows: number;
  active_workflows: number;
  success_rate: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
}

export interface ApplicationResponse {
  id: number;
  company: string;
  role: string;
  status: string;
  priority: string;
  source_url?: string | null;
  source_platform?: string | null;
  match_score?: number | null;
  location?: string | null;
  employment_type?: string | null;
  referral_status?: string | null;
  referral_contact_name?: string | null;
  follow_up_status?: string | null;
  next_follow_up_date?: string | null;
  applied_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface ApplicationListResponse {
  total: number;
  page: number;
  page_size: number;
  items: ApplicationResponse[];
}

export interface PipelineSummaryResponse {
  total_applications: number;
  status_counts: Record<string, number>;
  average_match_score: number;
  top_companies: Record<string, number>;
}

export interface FollowUpCategoryResponse {
  due_today: ApplicationResponse[];
  scheduled_future: ApplicationResponse[];
  overdue: ApplicationResponse[];
}

export interface ApplicationTimelineEventResponse {
  id: number;
  application_id: number;
  event_type: string;
  description: string;
  old_value?: string | null;
  new_value?: string | null;
  timestamp: string;
}

export interface InterviewResponse {
  id: number;
  application_id: number;
  round_number: number;
  stage_name: string;
  interview_type: string;
  scheduled_at?: string | null;
  status: string;
  notes?: string | null;
}

export interface DiscoveredJob {
  id: number;
  title: string;
  company: string;
  location?: string | null;
  is_remote?: boolean | null;
  provider: string;
  source_url: string;
  match_score?: number | null;
  salary_range?: string | null;
  skills_required: string[];
  status: string;
  discovered_at: string;
}

export interface OpportunityListResponse {
  total: number;
  items: DiscoveredJob[];
}

export interface JobSearchResponse {
  provider: string;
  query: string;
  location?: string | null;
  total_found: number;
  opportunities: DiscoveredJob[];
}

export interface OutcomeFeedbackResponse {
  id: number;
  application_id: number;
  outcome_type: string;
  feedback_stage: string;
  reasons_cited: string[];
  skills_passed: string[];
  skills_failed: string[];
  difficulty: string;
  experience: string;
  salary_offered?: number | null;
  notes?: string | null;
  created_at: string;
}

export interface AssetVersionResponse {
  id: number;
  application_id: number;
  workflow_id?: number | null;
  resume_summary?: string | null;
  customizations_applied: string[];
  asset_score_at_application?: number | null;
  created_at: string;
}

export interface FieldIssueResponse {
  id: number;
  application_id?: number | null;
  field_name: string;
  field_label?: string | null;
  platform: string;
  issue_type: string;
  error_message?: string | null;
  resolved: boolean;
  created_at: string;
}

export interface AnalyticsSummaryResponse {
  total_tracked: number;
  total_applied: number;
  total_interviews: number;
  total_offers: number;
  total_rejections: number;
  overall_conversion_rate: number;
  funnel: Record<string, any>;
  platform_metrics: PlatformPerformanceResponse[];
  active_signals_count: number;
}

export interface ConversionFunnelResponse {
  discovered: number;
  saved: number;
  applied: number;
  screen: number;
  technical: number;
  final_round: number;
  offers: number;
  accepted: number;
  rejected: number;
  conversion_rates: Record<string, number>;
}

export interface PlatformPerformanceResponse {
  platform: string;
  total_applications: number;
  screen_rate: number;
  offer_rate: number;
  rejection_rate: number;
  field_issue_count: number;
}

export interface FeedbackSignalResponse {
  id: number;
  signal_type: string;
  confidence: number;
  source_entity?: string | null;
  payload?: Record<string, any> | null;
  is_active: boolean;
  created_at: string;
}

export interface FeedbackRankResponse {
  base_score: number;
  adjusted_score: number;
  priority: string;
  recommendation: string;
  feedback_adjustments: string[];
  risk_flags: string[];
}

export interface MemoryResponse {
  memories: Record<string, string>;
  total_count: number;
}

export interface ChatHistoryItem {
  role: string;
  content: string;
}

export interface UserProfileResponse {
  id: number;
  name: string;
  email: string;
  title?: string | null;
  skills: string[];
  experience_years?: number | null;
  target_roles: string[];
  target_locations: string[];
}
