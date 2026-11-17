import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { CreditCard, CreditCardCreate, CreditCardUpdate } from "@/lib/types";

export const CARDS_QUERY_KEY = ["cards"];

/**
 * Hook to fetch the list of credit cards.
 */
export function useCards(includeArchived: boolean = false) {
  return useQuery<CreditCard[]>({
    queryKey: [...CARDS_QUERY_KEY, { includeArchived }],
    queryFn: () =>
      api.get<CreditCard[]>(
        `/cards${includeArchived ? "?include_archived=true" : ""}`
      ),
  });
}

/**
 * Hook to fetch a single credit card by ID.
 */
export function useCard(id: string | null) {
  return useQuery<CreditCard>({
    queryKey: [...CARDS_QUERY_KEY, id],
    queryFn: () => api.get<CreditCard>(`/cards/${id}`),
    enabled: Boolean(id),
  });
}

/**
 * Hook to create a new credit card.
 */
export function useCreateCard() {
  const queryClient = useQueryClient();

  return useMutation<CreditCard, Error, CreditCardCreate>({
    mutationFn: (newCard: CreditCardCreate) => api.post<CreditCard>("/cards", newCard),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CARDS_QUERY_KEY });
    },
  });
}

/**
 * Hook to update an existing credit card.
 */
export function useUpdateCard() {
  const queryClient = useQueryClient();

  return useMutation<CreditCard, Error, { id: string; data: CreditCardUpdate }>({
    mutationFn: ({ id, data }) => api.patch<CreditCard>(`/cards/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CARDS_QUERY_KEY });
    },
  });
}

/**
 * Hook to archive a credit card.
 */
export function useArchiveCard() {
  const queryClient = useQueryClient();

  return useMutation<CreditCard, Error, string>({
    mutationFn: (id: string) => api.post<CreditCard>(`/cards/${id}/archive`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CARDS_QUERY_KEY });
    },
  });
}
