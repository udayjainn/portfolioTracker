"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useInvestor(slug: string) {
  return useQuery({
    queryKey: ["investor", slug],
    queryFn: () => api.getInvestor(slug),
    enabled: !!slug,
  });
}

export function useInvestorHoldings(
  slug: string,
  params: { report_date?: string; sort?: string; change_type?: string; page?: number; limit?: number } = {},
) {
  return useQuery({
    queryKey: ["investor", slug, "holdings", params],
    queryFn: () => api.getInvestorHoldings(slug, params),
    enabled: !!slug,
  });
}
