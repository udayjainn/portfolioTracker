"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/formatters";
import { SkeletonCard } from "@/components/shared/SkeletonCard";

function SecurityRow({ item }: { item: Record<string, unknown> }) {
  const ticker = item.ticker as string;
  const name = item.name as string;
  const count = item.investor_count as number;
  const totalValue = item.total_value_usd as number;

  return (
    <div className="flex items-center justify-between border-b border-gray-100 py-3 last:border-0">
      <div>
        <span className="font-medium text-gray-900">{ticker}</span>
        <p className="text-sm text-gray-500">{name}</p>
      </div>
      <div className="text-right">
        <p className="font-medium text-gray-900">{formatCurrency(totalValue)}</p>
        <p className="text-xs text-gray-500">{formatNumber(count)} investors</p>
      </div>
    </div>
  );
}

export function MostBoughtSold({ country }: { country?: string }) {
  const bought = useQuery({
    queryKey: ["most-bought", country],
    queryFn: () => api.getMostBought({ country, limit: 5 }),
  });
  const sold = useQuery({
    queryKey: ["most-sold", country],
    queryFn: () => api.getMostSold({ country, limit: 5 }),
  });

  const loading = bought.isLoading || sold.isLoading;

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      <div className="rounded-lg border border-gray-200 bg-white p-5">
        <h3 className="mb-3 font-semibold text-green-700">Most Bought</h3>
        {bought.data?.map((item, i) => <SecurityRow key={i} item={item} />)}
        {!bought.data?.length && <p className="text-sm text-gray-400">No data yet</p>}
      </div>
      <div className="rounded-lg border border-gray-200 bg-white p-5">
        <h3 className="mb-3 font-semibold text-red-700">Most Sold</h3>
        {sold.data?.map((item, i) => <SecurityRow key={i} item={item} />)}
        {!sold.data?.length && <p className="text-sm text-gray-400">No data yet</p>}
      </div>
    </div>
  );
}
