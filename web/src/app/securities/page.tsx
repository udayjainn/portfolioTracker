"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { SkeletonCard } from "@/components/shared/SkeletonCard";

export default function SecuritiesPage() {
  const [page, setPage] = useState(1);
  const [ticker, setTicker] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["securities", page, ticker],
    queryFn: () =>
      api.getSecurities({
        country: "US",
        ticker: ticker || undefined,
        page,
        limit: 24,
      }),
  });

  const totalPages = data ? Math.ceil(data.meta.total / data.meta.limit) : 1;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold text-gray-900">Securities</h1>
      <p className="mb-6 text-sm text-gray-500">
        Stocks held by tracked US institutional investors (from 13F filings).
      </p>

      <input
        type="search"
        placeholder="Filter by ticker…"
        value={ticker}
        onChange={(e) => {
          setTicker(e.target.value);
          setPage(1);
        }}
        className="mb-6 w-full max-w-sm rounded-md border px-3 py-2 text-sm"
      />

      {isLoading && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {!isLoading && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data?.data.map((s) => (
              <Link
                key={s.id}
                href={`/securities/${s.ticker}`}
                className="rounded-lg border border-gray-200 bg-white px-4 py-3 hover:border-blue-300"
              >
                <p className="font-medium text-gray-900">{s.ticker}</p>
                <p className="truncate text-sm text-gray-500">{s.name}</p>
                <p className="mt-1 text-xs text-gray-400">{s.exchange}</p>
              </Link>
            ))}
          </div>

          {data?.meta.total === 0 && (
            <p className="text-sm text-gray-400">No securities yet. Run the data pipeline ingest.</p>
          )}

          {totalPages > 1 && (
            <div className="mt-8 flex items-center justify-center gap-4">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded border px-3 py-1 text-sm disabled:opacity-40"
              >
                Previous
              </button>
              <span className="text-sm text-gray-500">
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="rounded border px-3 py-1 text-sm disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
