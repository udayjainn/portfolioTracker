"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatCurrency, formatRelativeDate } from "@/lib/formatters";
import { ChangeIndicator } from "@/components/shared/ChangeIndicator";
import type { ChangeType } from "@/types/holding";
import { SkeletonCard } from "@/components/shared/SkeletonCard";

export function RecentActivity({ country }: { country?: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["activity", country],
    queryFn: () => api.getActivityFeed({ country, limit: 10 }),
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (!data?.data?.length) return <p className="text-sm text-gray-400">No recent activity</p>;

  return (
    <div className="space-y-3">
      {data.data.map((item, i) => (
        <div key={i} className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-gray-900">
              {item.investor_name as string}
            </p>
            <p className="text-xs text-gray-500">
              {item.change_type as string} {item.ticker as string} — {item.security_name as string}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ChangeIndicator type={item.change_type as ChangeType} />
            <div className="text-right">
              <p className="text-sm font-medium">{formatCurrency(item.value_usd as number)}</p>
              <p className="text-xs text-gray-400">{formatRelativeDate(item.report_date as string)}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
