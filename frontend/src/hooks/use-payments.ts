import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { CardBillStatus, Payment, PaymentCreate } from "@/lib/types";

export const PAYMENTS_QUERY_KEY = ["payments"];
export const BILLS_QUERY_KEY = ["payments", "bills"];

/**
 * Hook to fetch payments list with optional card and statement filters.
 */
export function usePayments(cardId?: string, statementId?: string) {
  const queryParams = new URLSearchParams();
  if (cardId) queryParams.set("card_id", cardId);
  if (statementId) queryParams.set("statement_id", statementId);

  const qs = queryParams.toString();
  const path = `/payments${qs ? `?${qs}` : ""}`;

  return useQuery<Payment[]>({
    queryKey: [...PAYMENTS_QUERY_KEY, { cardId, statementId }],
    queryFn: () => api.get<Payment[]>(path),
  });
}

/**
 * Hook to fetch live bills status across all credit cards.
 */
export function useCardBills() {
  return useQuery<CardBillStatus[]>({
    queryKey: BILLS_QUERY_KEY,
    queryFn: () => api.get<CardBillStatus[]>("/payments/bills"),
  });
}

/**
 * Hook to record a new bill payment.
 */
export function useRecordPayment() {
  const queryClient = useQueryClient();

  return useMutation<Payment, Error, PaymentCreate>({
    mutationFn: (newPayment: PaymentCreate) =>
      api.post<Payment>("/payments", newPayment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PAYMENTS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: BILLS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["cards"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

/**
 * Hook to delete/cancel a payment.
 */
export function useDeletePayment() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (id: string) => api.delete<void>(`/payments/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PAYMENTS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: BILLS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["cards"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}
