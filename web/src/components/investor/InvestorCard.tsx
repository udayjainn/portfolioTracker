import Link from "next/link";
import type { InvestorSummary } from "@/types/investor";
import { formatCurrency } from "@/lib/formatters";
import { CountryFlag } from "@/components/shared/CountryFlag";

export function InvestorCard({ investor }: { investor: InvestorSummary }) {
  return (
    <Link
      href={`/investors/${investor.slug}`}
      className="group block rounded-lg border border-gray-200 bg-white p-5 transition hover:border-blue-300 hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <h3 className="truncate font-semibold text-gray-900 group-hover:text-blue-600">
            {investor.name}
          </h3>
          <p className="mt-0.5 text-sm text-gray-500">{investor.investor_type}</p>
        </div>
        <CountryFlag code={investor.country} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-400">Portfolio</p>
          <p className="font-bold text-gray-900">{formatCurrency(investor.portfolio_value_usd)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Holdings</p>
          <p className="font-bold text-gray-900">{investor.holdings_count}</p>
        </div>
      </div>
    </Link>
  );
}
