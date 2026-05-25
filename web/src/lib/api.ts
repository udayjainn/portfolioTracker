import type { PaginatedResponse, SearchResults, ApiError as ApiErrorType } from "@/types/api";
import type { InvestorDetail, InvestorSummary } from "@/types/investor";
import type { HoldingSummary } from "@/types/holding";
import type { SecurityDetail, SecuritySummary } from "@/types/security";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }

  return res.json();
}

function buildQuery(params: Record<string, string | number | undefined | null>): string {
  const filtered = Object.entries(params).filter(([, v]) => v != null && v !== "");
  if (filtered.length === 0) return "";
  return "?" + new URLSearchParams(filtered.map(([k, v]) => [k, String(v)])).toString();
}

export const api = {
  getInvestors(params: {
    country?: string;
    type?: string;
    sort?: string;
    page?: number;
    limit?: number;
  } = {}): Promise<PaginatedResponse<InvestorSummary>> {
    return request(`/api/v1/investors${buildQuery(params)}`);
  },

  getInvestor(slug: string): Promise<InvestorDetail> {
    return request(`/api/v1/investors/${slug}`);
  },

  getInvestorHoldings(
    slug: string,
    params: { report_date?: string; sort?: string; change_type?: string; page?: number; limit?: number } = {},
  ): Promise<PaginatedResponse<HoldingSummary>> {
    return request(`/api/v1/investors/${slug}/holdings${buildQuery(params)}`);
  },

  getTrendingInvestors(params: { country?: string; limit?: number } = {}): Promise<InvestorSummary[]> {
    return request(`/api/v1/investors/trending${buildQuery(params)}`);
  },

  getSecurity(ticker: string): Promise<SecurityDetail> {
    return request(`/api/v1/securities/${ticker}`);
  },

  getSecurityHolders(
    ticker: string,
    params: { sort?: string; page?: number; limit?: number } = {},
  ): Promise<PaginatedResponse<Record<string, unknown>>> {
    return request(`/api/v1/securities/${ticker}/holders${buildQuery(params)}`);
  },

  getMostBought(params: { country?: string; limit?: number } = {}): Promise<Record<string, unknown>[]> {
    return request(`/api/v1/securities/most-bought${buildQuery(params)}`);
  },

  getMostSold(params: { country?: string; limit?: number } = {}): Promise<Record<string, unknown>[]> {
    return request(`/api/v1/securities/most-sold${buildQuery(params)}`);
  },

  search(query: string, type?: string): Promise<SearchResults> {
    return request(`/api/v1/search${buildQuery({ q: query, type })}`);
  },

  autocomplete(query: string): Promise<{ suggestions: string[] }> {
    return request(`/api/v1/search/autocomplete${buildQuery({ q: query })}`);
  },

  getActivityFeed(params: { country?: string; page?: number; limit?: number } = {}): Promise<PaginatedResponse<Record<string, unknown>>> {
    return request(`/api/v1/activity/feed${buildQuery(params)}`);
  },

  compareInvestors(slugs: string[], report_date?: string): Promise<Record<string, unknown>> {
    return request(`/api/v1/compare${buildQuery({ investors: slugs.join(","), report_date })}`);
  },
};
