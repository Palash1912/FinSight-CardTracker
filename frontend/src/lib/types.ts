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

/** Transaction representation (Phase 3). */
export interface Transaction {
  id: string;
  card_id: string;
  date: string;
  description: string;
  amount: Money;
  category: string;
  type: "debit" | "credit";
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
