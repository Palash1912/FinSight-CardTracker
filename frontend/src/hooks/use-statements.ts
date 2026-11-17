import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  Statement,
  StatementReviewDetail,
  StatementConfirmRequest,
} from "@/lib/types";

export const STATEMENTS_QUERY_KEY = ["statements"];

/**
 * Hook to list statements, optionally filtered by card.
 */
export function useStatements(cardId?: string) {
  return useQuery<Statement[]>({
    queryKey: [...STATEMENTS_QUERY_KEY, { cardId }],
    queryFn: () =>
      api.get<Statement[]>(
        `/statements${cardId ? `?card_id=${cardId}` : ""}`
      ),
  });
}

/**
 * Hook to get statement review details by ID.
 */
export function useStatementReview(id: string | null) {
  return useQuery<StatementReviewDetail>({
    queryKey: [...STATEMENTS_QUERY_KEY, "review", id],
    queryFn: () => api.get<StatementReviewDetail>(`/statements/${id}`),
    enabled: Boolean(id),
  });
}

/**
 * Hook to upload a statement PDF.
 */
export function useUploadStatement() {
  const queryClient = useQueryClient();

  return useMutation<
    StatementReviewDetail,
    Error,
    { file: File; cardId?: string }
  >({
    mutationFn: async ({ file, cardId }) => {
      const formData = new FormData();
      formData.append("file", file);
      if (cardId) {
        formData.append("card_id", cardId);
      }
      return api.post<StatementReviewDetail>("/statements/upload", formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: STATEMENTS_QUERY_KEY });
    },
  });
}

/**
 * Hook to confirm statement import.
 */
export function useConfirmStatement() {
  const queryClient = useQueryClient();

  return useMutation<
    Statement,
    Error,
    { id: string; request: StatementConfirmRequest }
  >({
    mutationFn: ({ id, request }) =>
      api.post<Statement>(`/statements/${id}/confirm`, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: STATEMENTS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["cards"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    },
  });
}

/**
 * Hook to delete/rollback a statement and its transactions.
 */
export function useDeleteStatement() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (id: string) => api.delete<void>(`/statements/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: STATEMENTS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    },
  });
}
