/**
 * API types. Field names are snake_case to match the FastAPI/Pydantic responses.
 * Money values are decimal strings (e.g. "150000.0000") — parse with Number()
 * only for display, never for arithmetic.
 */

export type Money = string;

/** Health check response from the backend API. */
export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export type CardNetwork = "visa" | "mastercard" | "amex" | "rupay" | "diners_club";
export type CardStatus = "active" | "archived";

/** Credit card as returned by GET /api/v1/cards. */
export interface CreditCard {
  id: string;
  issuer: string;
  card_name: string;
  network: CardNetwork;
  last_four_digits: string;
  billing_cycle_day: number;
  payment_due_days: number;
  credit_limit: Money;
  current_balance: Money;
  available_credit: Money;
  annual_fee: Money;
  status: CardStatus;
  next_statement_date: string;
  next_due_date: string;
  created_at: string;
  updated_at: string | null;
}

/** Body for POST /api/v1/cards. */
export interface CreditCardCreate {
  issuer: string;
  card_name: string;
  network: CardNetwork;
  last_four_digits: string;
  billing_cycle_day: number;
  payment_due_days: number;
  credit_limit: Money;
  current_balance?: Money;
  annual_fee?: Money;
}

/** Body for PATCH /api/v1/cards/{id}. Only the fields sent are changed. */
export type CreditCardUpdate = Partial<CreditCardCreate> & { status?: CardStatus };

/** Dashboard metric card data. */
export interface DashboardMetric {
  label: string;
  value: string;
  change?: string;
  icon: string;
}

/** Transaction representation. */
export interface Transaction {
  id: string;
  user_id: string;
  card_id: string;
  statement_id: string | null;
  transaction_date: string;
  posting_date: string | null;
  original_description: string;
  cleaned_description: string;
  merchant_name: string | null;
  category: string;
  amount: Money;
  currency: string;
  txn_type: "debit" | "credit";
  fingerprint: string;
  source: string;
  status: "pending" | "posted" | "reconciled";
  source_page?: number | null;
  source_row?: number | null;
  created_at: string;
  updated_at: string | null;
}

export type StatementStatus = "pending_review" | "imported" | "rejected" | "failed";

/** Statement representation. */
export interface Statement {
  id: string;
  user_id: string;
  card_id: string;
  statement_date: string;
  due_date: string;
  period_start: string | null;
  period_end: string | null;
  total_amount_due: Money;
  minimum_amount_due: Money;
  opening_balance: Money;
  closing_balance: Money;
  total_credits: Money;
  total_debits: Money;
  file_name: string;
  file_size_bytes: number;
  parser_used: string;
  status: StatementStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string | null;
}

/** Detailed statement for the review & reconciliation screen. */
export interface StatementReviewDetail extends Statement {
  transactions: Transaction[];
  reconciliation_matched: boolean;
  net_calculated: Money;
}

/** Request body to confirm statement import. */
export interface StatementConfirmRequest {
  excluded_transaction_ids?: string[];
  update_card_balance?: boolean;
}

/** Generic paginated response. */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** Generic API message response. */
export interface MessageResponse {
  message: string;
}

export type PaymentMethod =
  | "upi"
  | "neft"
  | "imps"
  | "net_banking"
  | "debit_card"
  | "auto_debit"
  | "cheque"
  | "cash"
  | "other";

export type BillStatus = "PAID" | "PARTIALLY_PAID" | "UNPAID" | "NO_BILL";

/** Payment record representation. */
export interface Payment {
  id: string;
  user_id: string;
  card_id: string;
  statement_id: string | null;
  payment_date: string;
  amount: Money;
  currency: string;
  payment_method: PaymentMethod;
  reference_number: string | null;
  notes: string | null;
  status: "completed" | "pending" | "failed";
  created_at: string;
}

/** Body for recording a payment. */
export interface PaymentCreate {
  card_id: string;
  statement_id?: string | null;
  payment_date: string;
  amount: Money;
  payment_method?: PaymentMethod;
  reference_number?: string | null;
  notes?: string | null;
}

/** Active bill status for each credit card. */
export interface CardBillStatus {
  card_id: string;
  card_name: string;
  issuer: string;
  last_four_digits: string;
  statement_id: string | null;
  statement_date: string | null;
  due_date: string;
  statement_amount: Money;
  minimum_due: Money;
  total_paid: Money;
  remaining_balance: Money;
  days_until_due: number;
  status: BillStatus;
  is_overdue: boolean;
}

/** Monthly spend point. */
export interface MonthlySpendPoint {
  month: string;
  total_spend: Money;
  transaction_count: number;
}

/** Category spend breakdown point. */
export interface CategorySpendPoint {
  category: string;
  total_spend: Money;
  percentage: number;
}

/** Top merchant spend item. */
export interface MerchantSpendPoint {
  merchant: string;
  total_spend: Money;
  transaction_count: number;
}

/** Card spend distribution point. */
export interface CardSpendPoint {
  card_id: string;
  card_name: string;
  issuer: string;
  total_spend: Money;
}

/** Comprehensive dashboard summary. */
export interface DashboardSummary {
  total_outstanding: Money;
  total_credit_limit: Money;
  total_available_credit: Money;
  overall_utilization: number;
  active_cards_count: number;
  current_month_spend: Money;
  previous_month_spend: Money;
  spend_change_percentage: number | null;
  upcoming_dues_count: number;
  upcoming_dues_total: Money;
}

/** Phase 5: Rewards types */

export interface RewardCapRead {
  id: string;
  rule_id: string;
  cap_name: string;
  cap_period: string;
  reset_basis: string;
  cap_amount: Money;
  cap_currency: string;
  pending_consumes_cap: boolean;
  refunds_reverse_cap: boolean;
}

export interface RewardRuleRead {
  id: string;
  program_id: string;
  rule_name: string;
  rule_type: string;
  reward_rate: Money;
  reward_rate_type: string;
  min_transaction_amount: Money;
  max_eligible_amount: Money | null;
  category: string | null;
  merchant_pattern: string | null;
  channel: string | null;
  exclusions: string[] | null;
  effective_from: string;
  effective_to: string | null;
  version: number;
  source_url: string | null;
  verification_status: string;
  confidence_notes: string | null;
  caps: RewardCapRead[];
}

export interface RewardProgramRead {
  id: string;
  card_id: string;
  program_name: string;
  reward_type: string;
  reward_currency: string;
  point_value_inr: Money;
  expiry_months: number | null;
  rules: RewardRuleRead[];
}

export interface CardRecommendationRequest {
  amount: Money;
  merchant?: string;
  category?: string;
  channel?: "online" | "offline" | "any";
  purchase_date?: string;
}

export interface CardRecommendationItem {
  card_id: string;
  card_name: string;
  issuer: string;
  network: string;
  last_four_digits: string;
  is_recommended: boolean;
  rank: number;
  effective_rate_percent: number;
  estimated_reward: Money;
  inr_value: Money;
  reward_type: string;
  rule_applied: string;
  remaining_cap_before: Money | null;
  remaining_cap_after: Money | null;
  cap_period: string | null;
  explanation: string;
  verification_status: string;
  confidence_notes: string | null;
}

export interface CardRecommendationResponse {
  best_card: CardRecommendationItem | null;
  cards: CardRecommendationItem[];
  purchase_amount: Money;
  disclaimer: string;
}

export interface CapUtilizationItem {
  card_id: string;
  card_name: string;
  issuer: string;
  cap_name: string;
  cap_period: string;
  reset_basis: string;
  cap_amount: Money;
  consumed_amount: Money;
  remaining_amount: Money;
  utilization_percentage: number;
  next_reset_date: string;
}

export interface RewardSummaryOverview {
  total_cashback_earned: Money;
  total_points_balance: number;
  total_inr_value: Money;
  active_programs_count: number;
}

export interface RewardReconcileRequest {
  card_id?: string | null;
  statement_id?: string | null;
  force_recalculate?: boolean;
}

export interface RewardReconciliationItem {
  transaction_id: string;
  card_id: string;
  card_name: string;
  transaction_date: string;
  description: string;
  merchant_name: string | null;
  category: string;
  amount: Money;
  txn_type: "debit" | "credit";
  rule_name: string | null;
  rate_percent: number;
  reward_amount: Money;
  inr_value: Money;
  status: string;
  is_discrepancy: boolean;
  discrepancy_reason: string | null;
  period_key: string | null;
  notes: string | null;
}

export interface RewardReconciliationSummary {
  total_transactions: number;
  total_spend: Money;
  total_rewards_inr: Money;
  total_excluded_spend: Money;
  total_capped_lost_inr: Money;
  discrepancy_count: number;
  items: RewardReconciliationItem[];
}

/** Phase 7: Email & Gmail statement ingestion types */

export interface EmailConnectionRead {
  id: string;
  email_address: string;
  provider: string;
  sync_status: "idle" | "syncing" | "error" | "disconnected";
  last_synced_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface EmailImportRead {
  id: string;
  connection_id: string;
  statement_id: string | null;
  card_id: string | null;
  sender: string;
  subject: string;
  received_at: string;
  attachment_name: string;
  status: "discovered" | "downloaded" | "ingested" | "skipped_duplicate" | "failed";
  error_message: string | null;
  created_at: string;
}

export interface GmailAuthUrlResponse {
  auth_url: string;
  state: string;
}

export interface GmailSyncRequest {
  connection_id?: string | null;
  days_back?: number;
}

export interface GmailSyncResponse {
  connection_id: string;
  email_address: string;
  messages_found: number;
  attachments_downloaded: number;
  statements_created: number;
  duplicates_skipped: number;
  errors: string[];
}

/** Phase 8: AI Financial Assistant types */

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  tool_calls?: Array<{ tool: string; args?: Record<string, unknown>; result?: unknown }> | null;
  tool_call_id?: string | null;
  created_at: string;
}

export interface AIConversation {
  id: string;
  title: string;
  created_at: string;
  updated_at?: string | null;
  messages: ChatMessage[];
}

export interface ChatRequest {
  conversation_id?: string | null;
  message: string;
}

export interface ChatResponse {
  conversation_id: string;
  message: ChatMessage;
  tool_calls_executed: Array<{ tool: string; args?: Record<string, unknown>; result?: unknown }>;
}




