import Link from "next/link";
import type { InvestorSummary } from "@/types/investor";
import { formatCurrency } from "@/lib/formatters";
import { CountryFlag } from "@/components/shared/CountryFlag";
import {
  investorDisplaySubtitle,
  investorDisplayTitle,
  investorTypeLabel,
} from "@/lib/investorDisplay";

export function InvestorCard({ investor }: { investor: InvestorSummary }) {
  const isInstitution = investor.investor_type === "INSTITUTIONAL";

  return (
    <Link
      href={`/investors/${investor.slug}`}
      className="group block rounded-lg border border-gray-200 bg-white p-5 transition hover:border-blue-300 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="truncate font-semibold text-gray-900 group-hover:text-blue-600">
            {investorDisplayTitle(investor)}
          </h3>
          <p className="mt-0.5 truncate text-sm text-gray-500">
            {investorDisplaySubtitle(investor)}
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              isInstitution ? "bg-violet-100 text-violet-800" : "bg-blue-100 text-blue-800"
            }`}
          >
            {investorTypeLabel(investor.investor_type)}
          </span>
          <CountryFlag code={investor.country} />
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-400">Portfolio</p>
          <p className="font-bold text-gray-900">{formatCurrency(investor.total_holdings_value)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Holdings</p>
          <p className="font-bold text-gray-900">{investor.positions_count ?? "—"}</p>
        </div>
      </div>
    </Link>
  );
}
