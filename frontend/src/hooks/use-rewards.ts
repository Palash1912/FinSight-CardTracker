import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  CapUtilizationItem,
  CardRecommendationRequest,
  CardRecommendationResponse,
  RewardProgramRead,
  RewardSummaryOverview,
} from "@/lib/types";

export const REWARDS_SUMMARY_KEY = ["rewards", "summary"];
export const REWARDS_CAPS_KEY = ["rewards", "caps"];
export const REWARDS_PROGRAMS_KEY = ["rewards", "programs"];

/**
 * Fetch high-level reward balances and stats.
 */
export function useRewardSummary() {
  return useQuery<RewardSummaryOverview>({
    queryKey: REWARDS_SUMMARY_KEY,
    queryFn: () => api.get<RewardSummaryOverview>("/rewards/summary"),
  });
}

/**
 * Fetch live cap utilization for all cards.
 */
export function useRewardCaps() {
  return useQuery<CapUtilizationItem[]>({
    queryKey: REWARDS_CAPS_KEY,
    queryFn: () => api.get<CapUtilizationItem[]>("/rewards/caps"),
  });
}

/**
 * Fetch configured reward programs with rules and caps.
 */
export function useRewardPrograms() {
  return useQuery<RewardProgramRead[]>({
    queryKey: REWARDS_PROGRAMS_KEY,
    queryFn: () => api.get<RewardProgramRead[]>("/rewards/programs"),
  });
}

/**
 * Evaluate and rank cards for a planned purchase.
 */
export function useRecommendCard() {
  return useMutation<CardRecommendationResponse, Error, CardRecommendationRequest>({
    mutationFn: (req: CardRecommendationRequest) =>
      api.post<CardRecommendationResponse>("/rewards/recommend", req),
  });
}

/**
 * Seed realistic bank reward rules fixture for user cards.
 */
export function useSeedRewards() {
  const queryClient = useQueryClient();

  return useMutation<{ status: string; message: string; seeded_count: number }, Error, void>({
    mutationFn: () => api.post("/rewards/seed", {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: REWARDS_PROGRAMS_KEY });
      queryClient.invalidateQueries({ queryKey: REWARDS_CAPS_KEY });
      queryClient.invalidateQueries({ queryKey: REWARDS_SUMMARY_KEY });
    },
  });
}
