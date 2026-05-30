/** JSON from FastAPI often serializes Decimal fields as strings. */
export type NumericInput = number | string | null | undefined;

export function toNumber(value: NumericInput): number | null {
  if (value == null || value === "") return null;
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function formatCurrency(value: NumericInput, currency = "USD"): string {
  const num = toNumber(value);
  if (num == null) return "N/A";
  const abs = Math.abs(num);
  const sign = num < 0 ? "-" : "";
  const symbol = currency === "USD" ? "$" : currency;

  if (abs >= 1e12) return `${sign}${symbol}${(abs / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `${sign}${symbol}${(abs / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${sign}${symbol}${(abs / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${sign}${symbol}${(abs / 1e3).toFixed(1)}K`;
  return `${sign}${symbol}${abs.toFixed(2)}`;
}

export function formatNumber(value: NumericInput): string {
  const num = toNumber(value);
  if (num == null) return "N/A";
  return new Intl.NumberFormat("en-US").format(num);
}

export function formatPercent(value: NumericInput): string {
  const num = toNumber(value);
  if (num == null) return "N/A";
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(1)}%`;
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/A";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatRelativeDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "today";
  if (diffDays === 1) return "yesterday";
  if (diffDays < 30) return `${diffDays} days ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  return `${Math.floor(diffDays / 365)} years ago`;
}

export function formatLargeNumber(value: NumericInput): string {
  const num = toNumber(value);
  if (num == null) return "N/A";
  const abs = Math.abs(num);
  if (abs >= 1e9) return `${(num / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${(num / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${(num / 1e3).toFixed(1)}K`;
  return num.toString();
}
