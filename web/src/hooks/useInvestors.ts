"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useInvestors(params: {
  country?: string;
  type?: string;
  sort?: string;
  page?: number;
  limit?: number;
} = {}) {
  return useQuery({
    queryKey: ["investors", params],
    queryFn: () => api.getInvestors(params),
  });
}

export function useTrendingInvestors(params: { country?: string; limit?: number } = {}) {
  return useQuery({
    queryKey: ["investors", "trending", params],
    queryFn: () => api.getTrendingInvestors(params),
  });
}
