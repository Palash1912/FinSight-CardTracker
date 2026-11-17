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
