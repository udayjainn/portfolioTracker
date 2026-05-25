"use client";

import Link from "next/link";
import { useTrendingInvestors } from "@/hooks/useInvestors";
import { formatCurrency } from "@/lib/formatters";
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

  if (!data?.length) return null;

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
                {investor.name}
              </h3>
              <p className="mt-0.5 text-sm text-gray-500">{investor.investor_type}</p>
            </div>
            <CountryFlag code={investor.country} />
          </div>
          <div className="mt-4 flex items-end justify-between">
            <div>
              <p className="text-xs text-gray-400">Portfolio Value</p>
              <p className="text-lg font-bold text-gray-900">
                {formatCurrency(investor.portfolio_value_usd)}
              </p>
            </div>
            <p className="text-sm text-gray-500">{investor.holdings_count} holdings</p>
          </div>
        </Link>
      ))}
    </div>
  );
}
