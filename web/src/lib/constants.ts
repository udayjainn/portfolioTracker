export const COUNTRIES = [
  { code: "US", name: "United States", flag: "🇺🇸" },
  { code: "CA", name: "Canada", flag: "🇨🇦" },
  { code: "GB", name: "United Kingdom", flag: "🇬🇧" },
  { code: "IN", name: "India", flag: "🇮🇳" },
] as const;

/** Matches DB / LLD: named managers vs asset managers & large institutions. */
export const INVESTOR_TYPES = [
  { value: "INDIVIDUAL", label: "Investors" },
  { value: "INSTITUTIONAL", label: "Institutions" },
] as const;

export const CHANGE_TYPE_CONFIG = {
  NEW: { label: "New", color: "text-blue-600", bg: "bg-blue-50" },
  INCREASED: { label: "Increased", color: "text-green-600", bg: "bg-green-50" },
  DECREASED: { label: "Decreased", color: "text-red-600", bg: "bg-red-50" },
  UNCHANGED: { label: "Unchanged", color: "text-gray-500", bg: "bg-gray-50" },
  SOLD: { label: "Sold", color: "text-orange-600", bg: "bg-orange-50" },
} as const;

export const SORT_OPTIONS = {
  investors: [
    { value: "name", label: "Name (A–Z)" },
    { value: "-total_value_usd", label: "Portfolio Value" },
    { value: "-total_positions", label: "Holdings Count" },
  ],
  holdings: [
    { value: "value_usd", label: "Value" },
    { value: "pct_of_portfolio", label: "% of Portfolio" },
    { value: "shares_change_pct", label: "Change %" },
  ],
} as const;

export const DEFAULT_PAGE_SIZE = 20;
