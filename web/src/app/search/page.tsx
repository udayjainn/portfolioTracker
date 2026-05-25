"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useSearch } from "@/hooks/useSearch";
import { formatCurrency } from "@/lib/formatters";
import { CountryFlag } from "@/components/shared/CountryFlag";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";

export default function SearchPage() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") ?? "";
  const [query, setQuery] = useState(initialQuery);
  const { data, isLoading } = useSearch(query);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Search</h1>

      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search investors, stocks, funds..."
        className="mb-8 w-full max-w-xl rounded-lg border border-gray-300 px-4 py-3 text-lg focus:border-blue-500 focus:outline-none"
        autoFocus
      />

      {isLoading && <LoadingSpinner className="py-12" />}

      {data && !data.investors.length && !data.securities.length && (
        <EmptyState title="No results found" description={`Nothing matched "${query}". Try a different search.`} />
      )}

      {data?.investors && data.investors.length > 0 && (
        <section className="mb-10">
          <h2 className="mb-3 text-lg font-semibold text-gray-900">Investors</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.investors.map((inv) => (
              <Link
                key={inv.id}
                href={`/investors/${inv.slug}`}
                className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 hover:border-blue-300"
              >
                <div>
                  <p className="font-medium text-gray-900">{inv.name}</p>
                  <p className="text-sm text-gray-500">{inv.investor_type}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{formatCurrency(inv.portfolio_value_usd)}</span>
                  <CountryFlag code={inv.country} />
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {data?.securities && data.securities.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-gray-900">Securities</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.securities.map((sec) => (
              <Link
                key={sec.id}
                href={`/securities/${sec.ticker}`}
                className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 hover:border-blue-300"
              >
                <div>
                  <p className="font-medium text-gray-900">{sec.ticker}</p>
                  <p className="text-sm text-gray-500">{sec.name}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{formatCurrency(sec.current_price, sec.currency)}</p>
                  <p className="text-xs text-gray-400">{sec.exchange}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
