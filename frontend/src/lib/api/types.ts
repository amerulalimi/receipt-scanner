export type ApiSuccessResponse<T> = {
  success: true;
  data: T;
  message: string | null;
};

export type ApiErrorResponse = {
  success: false;
  data: null;
  message: string;
  code: string;
};

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;

export type LoginData = {
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
  account_type: "individual" | "corporate";
  org_id: string | null;
  tax_year: number;
  tax_bracket: number | null;
  email_verified: boolean;
  available_contexts: Array<"individual" | "corporate">;
  active_context: "individual" | "corporate";
  active_role: string;
  active_org_id: string | null;
};

export type RegisterData = LoginData;

export type MeData = {
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
  account_type: "individual" | "corporate";
  org_id: string | null;
  org_name: string | null;
  tax_year: number;
  tax_bracket: number | null;
  email_verified: boolean;
  available_contexts: Array<"individual" | "corporate">;
  active_context: "individual" | "corporate";
  active_role: string;
  active_org_id: string | null;
  forwarding_address?: string | null;
};

export type AdminMeData = {
  admin_id: string;
  email: string;
  full_name: string | null;
};

export type VerifyEmailData = {
  email_verified: boolean;
};

export type SessionInfo = {
  session_id: string;
  ip: string;
  user_agent: string;
  created_at: string;
  last_active: string;
  is_current: boolean;
};

export type SecretSettingMasked = {
  key: string;
  masked_value: string | null;
  is_configured: boolean;
  updated_at: string | null;
};

export type SystemConfigItem = {
  key: string;
  value: string;
  is_default: boolean;
  updated_at: string | null;
};

export type OpenRouterHealthData = {
  configured: boolean;
  key_format_valid: boolean;
  auth_ok: boolean;
  model_ok: boolean;
  model: string | null;
  resolved_model: string | null;
  message: string;
  http_status: number | null;
};

export type OpenRouterModelOption = {
  id: string;
  name: string;
  prompt_price_per_million_usd: number;
  completion_price_per_million_usd: number;
  image_token_price_per_million_usd: number;
};

export type OpenRouterModelsData = {
  models: OpenRouterModelOption[];
  fetched_at: string | null;
  message: string | null;
};

export type AdminUserListItem = {
  id: string;
  full_name: string | null;
  account_type: "individual" | "corporate" | string;
  email: string;
  created_at: string;
  is_active: boolean;
};

export type AdminOrganizationListItem = {
  id: string;
  name: string;
  email_domain: string;
  status: "active" | "suspended" | string;
  employee_count: number;
  created_at: string;
};

export type AdminPaginatedUsersData = {
  items: AdminUserListItem[];
  page: number;
  limit: number;
  total: number;
  total_pages: number;
};

export type AdminPaginatedOrganizationsData = {
  items: AdminOrganizationListItem[];
  page: number;
  limit: number;
  total: number;
  total_pages: number;
};

export type RegistrationStatPoint = {
  period: string;
  label: string;
  count: number;
  cumulative: number;
};

export type RegistrationStatsData = {
  series: RegistrationStatPoint[];
  growth_percent: number;
  growth_label: string;
  total_in_range: number;
};

export type ClaimCategorySummary = {
  category: string;
  be_seksyen: string | null;
  limit: number;
  claimed: number;
  limit_amount?: number;
  total_claimed?: number;
  remaining: number;
  percentage: number;
  receipt_count: number;
  status: "ok" | "warning" | "full";
};

export type ClaimSummaryData = {
  tax_year: number;
  tax_bracket: number;
  estimated_savings: number;
  categories: ClaimCategorySummary[];
};

export type ClaimCompareData = {
  current_year: number;
  previous_year: number;
  current: ClaimSummaryData;
  previous: ClaimSummaryData;
};

export type CompletenessBreakdownItem = {
  criterion: string;
  achieved: boolean;
  points: number;
};

export type CompletenessScoreData = {
  tax_year: number;
  score: number;
  tracked_categories: number;
  total_categories: number;
  categories_with_claims: number;
  total_claimed: number | string;
  estimated_savings: number | string;
  milestone_message: string | null;
  next_action?: string | null;
  breakdown?: CompletenessBreakdownItem[];
};

export type ReadyToFileField = {
  step: number;
  category: string;
  be_seksyen: string;
  lhdn_section: string;
  lhdn_field_my: string;
  lhdn_field_en: string;
  amount: number | string;
  receipt_count: number;
};

export type ReadyToFileChecklistItem = {
  order: number;
  text_my: string;
  text_en: string;
};

export type ReadyToFileFilingItem = {
  be_field: string;
  be_seksyen: string;
  description: string;
  amount_to_enter: number | string;
  receipt_count: number;
  status: "ready" | "partial" | "empty";
};

export type ReadyToFileData = {
  tax_year: number;
  total_claimed: number | string;
  total_relief?: number | string;
  estimated_savings: number | string;
  tax_bracket: number;
  pending_review_count: number;
  fields: ReadyToFileField[];
  filing_checklist?: ReadyToFileFilingItem[];
  checklist: ReadyToFileChecklistItem[];
};

export type NotificationItem = {
  id: string;
  type: string;
  severity: "info" | "warning";
  title_my: string;
  title_en: string;
  message_my: string;
  message_en: string;
  action_href: string | null;
  created_at: string;
};

export type NotificationListData = {
  items: NotificationItem[];
  total: number;
};

export type NotificationPreferenceData = {
  email_enabled: boolean;
  in_app_enabled: boolean;
  digest_frequency: "off" | "monthly";
};

export type ReceiptUploadFileError = {
  filename: string | null;
  code: string;
  message: string;
};

export type ReceiptUploadData = {
  job_ids: string[];
  message: string;
  errors?: ReceiptUploadFileError[];
};

export type ReceiptListItem = {
  id: string;
  merchant_name: string | null;
  receipt_date: string | null;
  total_amount: number | string | null;
  claimed_amount: number | string | null;
  category: string | null;
  be_seksyen: string | null;
  status: string;
  scan_status?: string;
  ai_confidence: number | null;
  file_type: string | null;
  thumbnail_url: string | null;
  created_at: string;
};

export type ReceiptListData = {
  items: ReceiptListItem[];
  total: number;
  page: number;
  limit: number;
};

export type ReceiptFlagRead = {
  id: string;
  flag_type: string;
  message: string | null;
  resolved: boolean;
  created_at: string;
};

export type ReliefStatusInfo = {
  category: string;
  be_seksyen: string | null;
  limit_amount: number | string;
  total_claimed: number | string;
  remaining: number | string;
  percentage: number;
  status: "ok" | "warning" | "full";
};

export type ReceiptLineItem = {
  id: string;
  description: string;
  amount: number | string;
  category: string;
  ai_claimable: boolean;
  included_in_claim: boolean;
  sort_order: number;
};

export type ReceiptLineItemUpdatePayload = {
  id: string;
  included_in_claim: boolean;
  category?: string;
};

export type ReceiptDetail = {
  id: string;
  merchant_name: string | null;
  receipt_date: string | null;
  total_amount: number | string | null;
  claimed_amount: number | string | null;
  excluded_amount: number | string;
  category: string | null;
  be_seksyen: string | null;
  status: string;
  scan_status: string;
  ai_confidence: number | null;
  ai_nota: string | null;
  ocr_confidence: number | null;
  image_url: string | null;
  flags: ReceiptFlagRead[];
  line_items: ReceiptLineItem[];
  notes: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
  relief_status: ReliefStatusInfo | null;
};

export type ReceiptUpdatePayload = {
  category?: string;
  claimed_amount?: number;
  line_items?: ReceiptLineItemUpdatePayload[];
  notes?: string | null;
};

export type UploadSessionCreateData = {
  token: string;
  upload_url: string;
  qr_data: string;
  inactivity_timeout: number;
  expires_at: string;
};

export type UploadSessionValidateData = {
  valid: boolean;
  user_name: string;
  uploads_so_far: number;
  inactivity_remaining: number;
};

export type UploadSessionUploadData = {
  job_id: string;
  session_inactivity_reset: boolean;
  new_inactivity_remaining: number;
};

export type UploadSessionKeepAliveData = {
  inactivity_remaining: number;
};

export type UploadSessionCloseData = {
  uploads_count: number;
  message: string;
};

export const WSEventType = {
  receiptAdded: "receipt_added",
  receiptScanUpdated: "receipt_scan_updated",
  receiptFailed: "receipt_failed",
  sessionWarned: "session_warned",
  sessionExpired: "session_expired",
  sessionClosed: "session_closed",
} as const;

export type WSEventTypeValue = (typeof WSEventType)[keyof typeof WSEventType];

export type QRSession = UploadSessionCreateData;
export type QRValidation = UploadSessionValidateData;

export type DashboardWsEvent =
  | { type: "subscribed"; data: { upload_session_token: string } }
  | { type: "receipt_added"; data: { receipt: Record<string, unknown> } }
  | {
      type: "receipt_scan_updated";
      data: { receipt_id: string; scan_status: string };
    }
  | { type: "session_warned"; data: { seconds_remaining: number } }
  | { type: "session_expired"; data: { reason: string } }
  | { type: "session_closed"; data: { uploads_count: number; total_amount: number } }
  | { type: "receipt_failed"; data: { job_id: string; reason: string } }
  | { type: "error"; data: { message: string } };

export type WSEvent = Exclude<
  DashboardWsEvent,
  { type: "subscribed" } | { type: "error" }
>;

export type OrgPolicyData = {
  allowed_categories: string[];
  require_hr_approval: boolean;
  max_receipts_per_month: number;
  tax_year: number;
};

export type OrgMeData = {
  org_id: string;
  name: string;
  ssm_number: string;
  email_domain: string;
  domain_verified: boolean;
  total_employees: number;
  policy: OrgPolicyData;
};

export type OrgRegisterData = {
  org_id: string;
  name: string;
  email_domain: string;
  domain_verified: boolean;
};

export type OrgEmployeeItem = {
  user_id: string;
  full_name: string | null;
  email: string;
  role: string;
  is_active: boolean;
  receipts_count: number;
  total_claimed: number | string;
  pending_count: number;
};

export type OrgEmployeeListData = {
  items: OrgEmployeeItem[];
  total: number;
  page: number;
  limit: number;
};

export type OrgPendingReceiptItem = {
  id: string;
  user_id: string;
  employee_name: string | null;
  employee_email: string;
  merchant_name: string | null;
  receipt_date: string | null;
  claimed_amount: number | null;
  category: string | null;
  be_seksyen: string | null;
  status: string;
  scan_status: string;
  created_at: string;
};

export type OrgPendingReceiptListData = {
  items: OrgPendingReceiptItem[];
  total: number;
  page: number;
  limit: number;
};

export type OrgBulkApproveData = {
  approved_count: number;
  skipped_count: number;
};

export type InviteCreateData = {
  invite_id?: string | null;
  email?: string | null;
  type: string;
  invite_url?: string | null;
  expires_at: string;
  invited_count?: number;
};

export type InviteValidateData = {
  valid: boolean;
  org_name?: string | null;
  role?: string | null;
  invited_email?: string | null;
  expires_at?: string | null;
};

export type InviteAcceptData = {
  user_id: string;
  email: string;
  role: string;
  org_id: string;
};

export type ReliefLimitItem = {
  id: string;
  category: string;
  be_seksyen: string | null;
  limit_amount: number;
  description_my: string | null;
  sort_order: number;
  is_active: boolean;
  updated_at: string;
};

export type ReliefCategoryItem = {
  category: string;
  label: string;
  be_seksyen: string | null;
};

export type AuditLogItem = {
  id: number;
  user_id: string | null;
  org_id: string | null;
  action: string;
  resource: string | null;
  resource_id: string | null;
  metadata: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
};

export type AuditLogListData = {
  items: AuditLogItem[];
  total: number;
  page: number;
  limit: number;
};

export type SystemOverviewData = {
  auth_rate_limit_max: number;
  auth_rate_limit_window_seconds: number;
  audit_retention_days: number;
  receipt_retention_days: number;
  receipt_queue_depth: number;
  total_audit_logs: number;
  total_users?: number;
  total_receipts?: number;
  total_orgs?: number;
  receipts_today?: number;
  storage_backend?: string;
  worker_status?: "running" | "stopped";
  redis_connected?: boolean;
  db_connected?: boolean;
};

export type RetentionPurgeData = {
  audit_logs_deleted: number;
  receipts_deleted: number;
  purged_receipts?: number;
  purged_sessions?: number;
  audit_retention_days: number;
  receipt_retention_days: number;
};

export type HouseholdCategorySummary = {
  category: string;
  claimed: number | string;
  receipt_count: number;
};

export type HouseholdMemberSummary = {
  user_id: string;
  full_name: string | null;
  email: string;
  tax_year: number;
  tax_bracket: number;
  total_claimed: number | string;
  categories: HouseholdCategorySummary[];
};

export type HouseholdCombinedSummary = {
  tax_year: number;
  combined_total_claimed: number | string;
  members: HouseholdMemberSummary[];
};

export type SpouseIncomingRequest = {
  id: string;
  requester_name: string | null;
  requester_email: string;
  created_at: string;
};

export type SpouseOutgoingRequest = {
  id: string;
  partner_email: string;
  created_at: string;
};

export type HouseholdOverviewData = {
  accepted_link_id: string | null;
  partner: HouseholdMemberSummary | null;
  combined: HouseholdCombinedSummary | null;
  incoming_requests: SpouseIncomingRequest[];
  outgoing_request: SpouseOutgoingRequest | null;
};

export type ClaimSuggestionData = {
  receipt_id: string;
  category: string;
  suggested_user_id: string;
  suggestion?: "self" | "spouse";
  reason_my: string;
  reason_en: string;
  reason?: string;
  user_remaining: number | string;
  spouse_remaining: number | string;
  my_bracket?: number | null;
  spouse_bracket?: number | null;
};

export type OrgAnalyticsCategoryTrend = {
  category: string;
  month: string | null;
  total_claimed: number | string;
};

export type OrgAnalyticsEmployeeRank = {
  user_id: string;
  full_name: string | null;
  email: string;
  total_claimed: number | string;
  receipt_count: number;
};

export type OrgAnalyticsTurnaround = {
  average_hours: number;
  reviewed_count: number;
};

export type OrgAnalyticsRejectionReason = {
  reason: string;
  count: number;
};

export type OrgAnalyticsForecast = {
  category: string;
  approved_to_date: number | string;
  projected_year_end: number | string;
  org_limit: number | string;
  utilization_pct: number;
};

export type OrgAnalyticsData = {
  tax_year: number;
  category_trend: OrgAnalyticsCategoryTrend[];
  top_employees: OrgAnalyticsEmployeeRank[];
  turnaround: OrgAnalyticsTurnaround;
  rejections: OrgAnalyticsRejectionReason[];
  forecast: OrgAnalyticsForecast[];
};

export type OrgEmployeeBulkImportRow = {
  email: string;
  full_name?: string | null;
  employee_code?: string | null;
};

export type OrgEmployeeBulkImportData = {
  invited_count: number;
  invite_url: string | null;
};
