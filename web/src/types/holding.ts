export interface SecurityBrief {
  id: number;
  ticker: string;
  name: string;
  exchange: string;
  asset_type: string;
}

export type ChangeType = "NEW" | "INCREASED" | "DECREASED" | "UNCHANGED" | "SOLD";

export interface HoldingSummary {
  security: SecurityBrief;
  shares: number;
  value_usd: number;
  pct_of_portfolio: number;
  change_type: ChangeType;
  shares_change: number;
  shares_change_pct: number | null;
}
