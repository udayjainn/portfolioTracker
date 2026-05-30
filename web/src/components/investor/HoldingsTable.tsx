"use client";

import { useState } from "react";
import { useInvestorHoldings } from "@/hooks/useInvestor";
import { formatCurrency, formatPercent, formatNumber, toNumber } from "@/lib/formatters";
import { securityDisplaySubtitle, securityDisplayTitle } from "@/lib/securityDisplay";
import { ChangeIndicator } from "@/components/shared/ChangeIndicator";
import { Pagination } from "@/components/shared/Pagination";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

export function HoldingsTable({ slug }: { slug: string }) {
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState("-value_usd");
  const { data, isLoading } = useInvestorHoldings(slug, { sort, page, limit: 25 });

  if (isLoading) return <LoadingSpinner className="py-8" />;
  if (!data?.data?.length) {
    return (
      <p className="py-8 text-center text-gray-500">
        No 13F holdings yet. Data appears after the next SEC filing ingest for this investor.
      </p>
    );
  }

  return (
    <div>
      <div className="mb-3 flex justify-end">
        <select
          value={sort}
          onChange={(e) => { setSort(e.target.value); setPage(1); }}
          className="rounded-md border px-3 py-1.5 text-sm"
        >
          <option value="-value_usd">Value (largest first)</option>
          <option value="-pct_of_portfolio">% of Portfolio</option>
          <option value="-shares_change_pct">Change %</option>
        </select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="pb-2 font-medium">Security</th>
              <th className="pb-2 font-medium">Shares</th>
              <th className="pb-2 font-medium">Value</th>
              <th className="pb-2 font-medium">% Portfolio</th>
              <th className="pb-2 font-medium">Change</th>
            </tr>
          </thead>
          <tbody>
            {data.data.map((h) => {
              const sharesChange = toNumber(h.shares_change) ?? 0;
              return (
              <tr key={`${h.security.id}-${h.shares}-${h.value_usd}`} className="border-b border-gray-100">
                <td className="py-3">
                  <span className="font-medium text-gray-900">{securityDisplayTitle(h.security)}</span>
                  <p className="text-xs text-gray-500">{securityDisplaySubtitle(h.security)}</p>
                </td>
                <td className="py-3 text-gray-700">{formatNumber(h.shares)}</td>
                <td className="py-3 font-medium text-gray-900">{formatCurrency(h.value_usd)}</td>
                <td className="py-3 text-gray-700">{formatPercent(h.pct_of_portfolio)}</td>
                <td className="py-3">
                  <ChangeIndicator type={h.change_type} />
                  {sharesChange !== 0 && (
                    <span className="ml-2 text-xs text-gray-500">
                      {sharesChange > 0 ? "+" : ""}{formatNumber(sharesChange)}
                    </span>
                  )}
                </td>
              </tr>
            );
            })}
          </tbody>
        </table>
      </div>
      <Pagination meta={data.meta} onPageChange={setPage} />
    </div>
  );
}
