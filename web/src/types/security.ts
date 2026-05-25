export interface SecuritySummary {
  id: number;
  ticker: string;
  name: string;
  exchange: string;
  country: string;
  sector: string | null;
  asset_type: string;
  current_price: number | null;
  market_cap_usd: number | null;
  currency: string;
}

export interface SecurityDetail extends SecuritySummary {
  industry: string | null;
  isin: string | null;
  cusip: string | null;
  sedol: string | null;
}
