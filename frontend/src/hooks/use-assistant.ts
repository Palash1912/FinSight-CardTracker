import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  AIConversation,
  ChatRequest,
  ChatResponse,
} from "@/lib/types";

export const CONVERSATIONS_KEY = ["assistant", "conversations"];

/**
 * Fetch all advisory conversations for current user.
 */
export function useConversations() {
  return useQuery<AIConversation[]>({
    queryKey: CONVERSATIONS_KEY,
    queryFn: () => api.get<AIConversation[]>("/assistant/conversations"),
  });
}

/**
 * Fetch a single conversation and its full message history.
 */
export function useConversation(id?: string | null) {
  return useQuery<AIConversation>({
    queryKey: [...CONVERSATIONS_KEY, id],
    queryFn: () => api.get<AIConversation>(`/assistant/conversations/${id}`),
    enabled: Boolean(id),
  });
}

/**
 * Send a user message and receive the assistant's reply.
 */
export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation<ChatResponse, Error, ChatRequest>({
    mutationFn: (req: ChatRequest) => api.post<ChatResponse>("/assistant/chat", req),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY });
      queryClient.invalidateQueries({ queryKey: [...CONVERSATIONS_KEY, data.conversation_id] });
    },
  });
}

/**
 * Delete a conversation.
 */
export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (id: string) => api.delete<void>(`/assistant/conversations/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY });
    },
  });
}
