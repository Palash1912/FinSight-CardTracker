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
