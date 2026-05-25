import type { InvestorSummary } from "./investor";
import type { SecuritySummary } from "./security";

export interface PaginationMeta {
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface SearchResults {
  investors: InvestorSummary[];
  securities: SecuritySummary[];
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
