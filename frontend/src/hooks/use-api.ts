import { useQuery, useMutation, type UseMutationOptions } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { HealthResponse } from "@/lib/types";

/**
 * Hook to query the backend health endpoint.
 */
export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: () => api.get<HealthResponse>("/api/v1/health"),
    retry: false,
  });
}

/**
 * Generic hook for GET queries against the API.
 */
export function useApiQuery<T>(key: string[], path: string) {
  return useQuery<T>({
    queryKey: key,
    queryFn: () => api.get<T>(path),
  });
}

/**
 * Generic hook for mutations (POST, PUT, DELETE) against the API.
 */
export function useApiMutation<TData = unknown, TVariables = unknown>(
  path: string,
  method: "POST" | "PUT" | "DELETE" = "POST",
  options?: Omit<UseMutationOptions<TData, Error, TVariables>, "mutationFn">
) {
  return useMutation<TData, Error, TVariables>({
    mutationFn: async (variables: TVariables) => {
      switch (method) {
        case "POST":
          return api.post<TData>(path, variables);
        case "PUT":
          return api.put<TData>(path, variables);
        case "DELETE":
          return api.delete<TData>(path);
      }
    },
    ...options,
  });
}
