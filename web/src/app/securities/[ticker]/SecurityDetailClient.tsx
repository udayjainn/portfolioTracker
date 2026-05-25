"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { formatCurrency, formatLargeNumber } from "@/lib/formatters";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Pagination } from "@/components/shared/Pagination";
import { useState } from "react";

export function SecurityDetailClient({ ticker }: { ticker: string }) {
  const { data: security, isLoading } = useQuery({
    queryKey: ["security", ticker],
    queryFn: () => api.getSecurity(ticker),
  });

  const [page, setPage] = useState(1);
  const { data: holders } = useQuery({
    queryKey: ["security", ticker, "holders", page],
    queryFn: () => api.getSecurityHolders(ticker, { page, limit: 20 }),
  });

  if (isLoading) return <LoadingSpinner className="py-20" />;
  if (!security) return <p className="py-20 text-center text-gray-500">Security not found.</p>;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{security.ticker}</h1>
        <p className="mt-1 text-lg text-gray-500">{security.name}</p>
      </div>

      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <InfoCard label="Exchange" value={security.exchange} />
        <InfoCard label="Sector" value={security.sector ?? "N/A"} />
        <InfoCard label="Price" value={formatCurrency(security.current_price, security.currency)} />
        <InfoCard label="Market Cap" value={formatLargeNumber(security.market_cap_usd)} />
      </div>

      <h2 className="mb-4 text-xl font-semibold text-gray-900">Institutional Holders</h2>
      {holders?.data?.length ? (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2 font-medium">Investor</th>
                  <th className="pb-2 font-medium">Shares</th>
                  <th className="pb-2 font-medium">Value</th>
                  <th className="pb-2 font-medium">% of Portfolio</th>
                </tr>
              </thead>
              <tbody>
                {holders.data.map((h, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-3">
                      <Link href={`/investors/${h.investor_slug}`} className="font-medium text-blue-600 hover:underline">
                        {h.investor_name as string}
                      </Link>
                    </td>
                    <td className="py-3 text-gray-700">{formatLargeNumber(h.shares as number)}</td>
                    <td className="py-3 font-medium">{formatCurrency(h.value_usd as number)}</td>
                    <td className="py-3 text-gray-700">{(h.pct_of_portfolio as number)?.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination meta={holders.meta} onPageChange={setPage} />
        </>
      ) : (
        <p className="text-gray-400">No institutional holders found.</p>
      )}
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <p className="text-xs text-gray-400">{label}</p>
      <p className="mt-1 text-lg font-bold text-gray-900">{value}</p>
    </div>
  );
}
