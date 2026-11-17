import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Transaction } from "@/lib/types";

export interface TransactionFilters {
  cardId?: string;
  statementId?: string;
  category?: string;
  merchant?: string;
  txnType?: "debit" | "credit";
  search?: string;
  page?: number;
  pageSize?: number;
}

export interface TransactionsResponse {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
}

export const TRANSACTIONS_QUERY_KEY = ["transactions"];

export function useTransactions(filters: TransactionFilters = {}) {
  const queryParams = new URLSearchParams();
  if (filters.cardId) queryParams.set("card_id", filters.cardId);
  if (filters.statementId) queryParams.set("statement_id", filters.statementId);
  if (filters.category) queryParams.set("category", filters.category);
  if (filters.merchant) queryParams.set("merchant", filters.merchant);
  if (filters.txnType) queryParams.set("txn_type", filters.txnType);
  if (filters.search) queryParams.set("search", filters.search);
  if (filters.page) queryParams.set("page", String(filters.page));
  if (filters.pageSize) queryParams.set("page_size", String(filters.pageSize));

  const qs = queryParams.toString();
  const path = `/transactions${qs ? `?${qs}` : ""}`;

  return useQuery<TransactionsResponse>({
    queryKey: [...TRANSACTIONS_QUERY_KEY, filters],
    queryFn: () => api.get<TransactionsResponse>(path),
  });
}

export function useUpdateTransaction() {
  const queryClient = useQueryClient();

  return useMutation<
    Transaction,
    Error,
    { id: string; data: Partial<Pick<Transaction, "category" | "merchant_name" | "cleaned_description" | "status">> }
  >({
    mutationFn: ({ id, data }) => api.patch<Transaction>(`/transactions/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TRANSACTIONS_QUERY_KEY });
    },
  });
}

export function useDeleteTransaction() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (id: string) => api.delete<void>(`/transactions/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TRANSACTIONS_QUERY_KEY });
    },
  });
}
