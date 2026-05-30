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
  shares: number | string;
  value_usd: number | string;
  pct_of_portfolio: number | string;
  change_type: ChangeType;
  shares_change: number | string;
  shares_change_pct: number | string | null;
}
