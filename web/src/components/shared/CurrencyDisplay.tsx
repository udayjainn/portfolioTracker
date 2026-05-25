import { formatCurrency } from "@/lib/formatters";

export function CurrencyDisplay({
  value,
  currency = "USD",
  className = "",
}: {
  value: number | null | undefined;
  currency?: string;
  className?: string;
}) {
  return <span className={className}>{formatCurrency(value, currency)}</span>;
}
