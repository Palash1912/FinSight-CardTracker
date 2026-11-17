import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  DiscrepancyReportResponse,
  DocumentRead,
  PolicySearchRequest,
  PolicySearchResponse,
} from "@/lib/types";

export const DOCUMENTS_KEY = ["documents"];
export const DISCREPANCIES_KEY = ["documents", "discrepancies"];

/**
 * Fetch all ingested policy documents.
 */
export function useDocuments(cardId?: string) {
  const qs = cardId ? `?card_id=${cardId}` : "";
  return useQuery<DocumentRead[]>({
    queryKey: [...DOCUMENTS_KEY, cardId],
    queryFn: () => api.get<DocumentRead[]>(`/documents${qs}`),
  });
}

/**
 * Upload a new bank policy or agreement PDF.
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation<DocumentRead, Error, FormData>({
    mutationFn: (formData: FormData) => api.post<DocumentRead>("/documents/upload", formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
      queryClient.invalidateQueries({ queryKey: DISCREPANCIES_KEY });
    },
  });
}

/**
 * Delete a policy document.
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (id: string) => api.delete<void>(`/documents/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
      queryClient.invalidateQueries({ queryKey: DISCREPANCIES_KEY });
    },
  });
}

/**
 * Query policy knowledge base with grounded citations.
 */
export function useSearchPolicies() {
  return useMutation<PolicySearchResponse, Error, PolicySearchRequest>({
    mutationFn: (req: PolicySearchRequest) => api.post<PolicySearchResponse>("/documents/search", req),
  });
}

/**
 * Audit discrepancies between active rules and policy texts.
 */
export function useDiscrepancies(cardId?: string) {
  const qs = cardId ? `?card_id=${cardId}` : "";
  return useQuery<DiscrepancyReportResponse>({
    queryKey: [...DISCREPANCIES_KEY, cardId],
    queryFn: () => api.get<DiscrepancyReportResponse>(`/documents/discrepancies${qs}`),
  });
}

/**
 * Seed official bank policy fixtures.
 */
export function useSeedPolicies() {
  const queryClient = useQueryClient();

  return useMutation<{ status: string; message: string; seeded_count: number }, Error, void>({
    mutationFn: () => api.post("/documents/seed", {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
      queryClient.invalidateQueries({ queryKey: DISCREPANCIES_KEY });
    },
  });
}
