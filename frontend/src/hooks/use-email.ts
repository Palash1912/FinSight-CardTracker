import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  EmailConnectionRead,
  EmailImportRead,
  GmailAuthUrlResponse,
  GmailSyncRequest,
  GmailSyncResponse,
} from "@/lib/types";

export const EMAIL_CONNECTIONS_KEY = ["email", "connections"];
export const EMAIL_IMPORTS_KEY = ["email", "imports"];

/**
 * Fetch connected email accounts.
 */
export function useEmailConnections() {
  return useQuery<EmailConnectionRead[]>({
    queryKey: EMAIL_CONNECTIONS_KEY,
    queryFn: () => api.get<EmailConnectionRead[]>("/email/connections"),
  });
}

/**
 * Fetch Google OAuth authorization URL.
 */
export function useGmailAuthUrl() {
  return useQuery<GmailAuthUrlResponse>({
    queryKey: ["email", "auth-url"],
    queryFn: () => api.get<GmailAuthUrlResponse>("/email/auth-url"),
    enabled: false, // only fetch when user clicks Connect
  });
}

/**
 * Handle Google OAuth callback code.
 */
export function useGmailCallback() {
  const queryClient = useQueryClient();

  return useMutation<EmailConnectionRead, Error, { code: string; state?: string }>({
    mutationFn: (payload) => api.post<EmailConnectionRead>("/email/callback", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EMAIL_CONNECTIONS_KEY });
    },
  });
}

/**
 * Trigger statement sync from connected email.
 */
export function useSyncGmail() {
  const queryClient = useQueryClient();

  return useMutation<GmailSyncResponse, Error, GmailSyncRequest>({
    mutationFn: (req: GmailSyncRequest) => api.post<GmailSyncResponse>("/email/sync", req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EMAIL_CONNECTIONS_KEY });
      queryClient.invalidateQueries({ queryKey: EMAIL_IMPORTS_KEY });
      queryClient.invalidateQueries({ queryKey: ["statements"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

/**
 * Disconnect an email connection.
 */
export function useDeleteEmailConnection() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (id: string) => api.delete<void>(`/email/connections/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EMAIL_CONNECTIONS_KEY });
    },
  });
}

/**
 * Fetch audit list of discovered statement emails and attachments.
 */
export function useEmailImports(limit: number = 50) {
  return useQuery<EmailImportRead[]>({
    queryKey: [...EMAIL_IMPORTS_KEY, limit],
    queryFn: () => api.get<EmailImportRead[]>(`/email/imports?limit=${limit}`),
  });
}
