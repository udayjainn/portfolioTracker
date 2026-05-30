"use client";

import Link from "next/link";
import { useTrendingInvestors } from "@/hooks/useInvestors";
import { formatCurrency } from "@/lib/formatters";
import {
  investorDisplaySubtitle,
  investorDisplayTitle,
  investorTypeLabel,
} from "@/lib/investorDisplay";
import { CountryFlag } from "@/components/shared/CountryFlag";
import { SkeletonCard } from "@/components/shared/SkeletonCard";

export function TrendingInvestors({ country }: { country?: string }) {
  const { data, isLoading } = useTrendingInvestors({ country, limit: 6 });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (!data?.length) {
    return (
      <p className="text-sm text-gray-500">
        No trending moves yet. Try the <a href="/investors" className="text-blue-600 hover:underline">investors</a> page.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data.map((investor) => (
        <Link
          key={investor.id}
          href={`/investors/${investor.slug}`}
          className="group rounded-lg border border-gray-200 bg-white p-5 transition hover:border-blue-300 hover:shadow-md"
        >
          <div className="flex items-start justify-between">
            <div className="min-w-0">
              <h3 className="truncate font-semibold text-gray-900 group-hover:text-blue-600">
                {investorDisplayTitle(investor)}
              </h3>
              <p className="mt-0.5 truncate text-sm text-gray-500">
                {investorDisplaySubtitle(investor)}
              </p>
              <span className="mt-1 inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                {investorTypeLabel(investor.investor_type)}
              </span>
            </div>
            <CountryFlag code={investor.country} />
          </div>
          <div className="mt-4 flex items-end justify-between">
            <div>
              <p className="text-xs text-gray-400">Portfolio Value</p>
              <p className="text-lg font-bold text-gray-900">
                {formatCurrency(investor.total_holdings_value)}
              </p>
            </div>
            <p className="text-sm text-gray-500">{investor.positions_count ?? 0} holdings</p>
          </div>
        </Link>
      ))}
    </div>
  );
}
