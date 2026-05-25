export interface InvestorSummary {
  id: number;
  slug: string;
  name: string;
  photo_url: string | null;
  country: string;
  investor_type: string;
  firm_name: string | null;
  net_worth_usd: number | null;
  total_holdings_value: number | null;
  positions_count: number | null;
}

export interface SnapshotSummary {
  report_date: string;
  total_value_usd: number;
  total_positions: number;
}

export interface InvestorDetail extends InvestorSummary {
  bio: string | null;
  latest_filing_date: string | null;
  top_holdings: HoldingSummary[];
  sector_breakdown: Record<string, number>;
  portfolio_history: SnapshotSummary[];
}

import type { HoldingSummary } from "./holding";
