"use client";

import { useState } from "react";
import { useInvestors } from "@/hooks/useInvestors";
import { InvestorCard } from "./InvestorCard";
import { Pagination } from "@/components/shared/Pagination";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { DEFAULT_PAGE_SIZE } from "@/lib/constants";

export function InvestorGrid({
  country,
  type,
  sort,
}: {
  country?: string;
  type?: string;
  sort?: string;
}) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useInvestors({ country, type, sort, page, limit: DEFAULT_PAGE_SIZE });

  if (isLoading) return <LoadingSpinner className="py-16" />;
  if (!data?.data?.length) return <EmptyState title="No investors found" description="Try adjusting your filters." />;

  return (
    <div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.data.map((investor) => (
          <InvestorCard key={investor.id} investor={investor} />
        ))}
      </div>
      <Pagination meta={data.meta} onPageChange={setPage} />
    </div>
  );
}
