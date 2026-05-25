"use client";

import type { PaginationMeta } from "@/types/api";

export function Pagination({
  meta,
  onPageChange,
}: {
  meta: PaginationMeta;
  onPageChange: (page: number) => void;
}) {
  if (meta.total_pages <= 1) return null;

  const pages: number[] = [];
  const start = Math.max(1, meta.page - 2);
  const end = Math.min(meta.total_pages, meta.page + 2);
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <div className="flex items-center justify-center gap-2 py-4">
      <button
        onClick={() => onPageChange(meta.page - 1)}
        disabled={meta.page <= 1}
        className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-40"
      >
        Previous
      </button>
      {start > 1 && <span className="px-1 text-gray-400">...</span>}
      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onPageChange(p)}
          className={`rounded-md px-3 py-1.5 text-sm ${
            p === meta.page ? "bg-blue-600 text-white" : "border hover:bg-gray-50"
          }`}
        >
          {p}
        </button>
      ))}
      {end < meta.total_pages && <span className="px-1 text-gray-400">...</span>}
      <button
        onClick={() => onPageChange(meta.page + 1)}
        disabled={meta.page >= meta.total_pages}
        className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-40"
      >
        Next
      </button>
    </div>
  );
}
