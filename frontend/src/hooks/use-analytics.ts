import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  CardSpendPoint,
  CategorySpendPoint,
  DashboardSummary,
  MerchantSpendPoint,
  MonthlySpendPoint,
} from "@/lib/types";

export const ANALYTICS_QUERY_KEY = ["analytics"];

/**
 * Hook to fetch high-level dashboard metrics.
 */
export function useDashboardSummary() {
  return useQuery<DashboardSummary>({
    queryKey: [...ANALYTICS_QUERY_KEY, "summary"],
    queryFn: () => api.get<DashboardSummary>("/analytics/summary"),
  });
}

/**
 * Hook to fetch monthly spend trend.
 */
export function useMonthlySpend(cardId?: string) {
  const qs = cardId ? `?card_id=${cardId}` : "";
  return useQuery<MonthlySpendPoint[]>({
    queryKey: [...ANALYTICS_QUERY_KEY, "monthly", cardId],
    queryFn: () => api.get<MonthlySpendPoint[]>(`/analytics/monthly${qs}`),
  });
}

/**
 * Hook to fetch category spend breakdown.
 */
export function useCategorySpend(
  cardId?: string,
  startDate?: string,
  endDate?: string
) {
  const params = new URLSearchParams();
  if (cardId) params.set("card_id", cardId);
  if (startDate) params.set("start_date", startDate);
  if (endDate) params.set("end_date", endDate);
  const qs = params.toString() ? `?${params.toString()}` : "";

  return useQuery<CategorySpendPoint[]>({
    queryKey: [...ANALYTICS_QUERY_KEY, "categories", { cardId, startDate, endDate }],
    queryFn: () => api.get<CategorySpendPoint[]>(`/analytics/categories${qs}`),
  });
}

/**
 * Hook to fetch top merchants by spend.
 */
export function useTopMerchants(limit: number = 10, cardId?: string) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cardId) params.set("card_id", cardId);

  return useQuery<MerchantSpendPoint[]>({
    queryKey: [...ANALYTICS_QUERY_KEY, "merchants", { limit, cardId }],
    queryFn: () =>
      api.get<MerchantSpendPoint[]>(`/analytics/merchants?${params.toString()}`),
  });
}

/**
 * Hook to fetch card spend distribution.
 */
export function useCardSpend() {
  return useQuery<CardSpendPoint[]>({
    queryKey: [...ANALYTICS_QUERY_KEY, "cards"],
    queryFn: () => api.get<CardSpendPoint[]>("/analytics/cards"),
  });
}
