"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";

const MAX_COMPARE = 4;

export default function ComparePage() {
  const [selected, setSelected] = useState<string[]>([]);
  const slugsParam = selected.join(",");

  const { data: investors } = useQuery({
    queryKey: ["investors", "US"],
    queryFn: () => api.getInvestors({ country: "US", limit: 100 }),
  });

  const { data: comparison, isLoading, error } = useQuery({
    queryKey: ["compare", slugsParam],
    queryFn: () => api.compareInvestors(selected),
    enabled: selected.length >= 2,
  });

  const investorOptions = useMemo(() => investors?.data ?? [], [investors]);

  function toggle(slug: string) {
    setSelected((prev) => {
      if (prev.includes(slug)) return prev.filter((s) => s !== slug);
      if (prev.length >= MAX_COMPARE) return prev;
      return [...prev, slug];
    });
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold text-gray-900">Compare Investors</h1>
      <p className="mb-6 text-sm text-gray-500">
        Select 2–{MAX_COMPARE} US funds to see overlapping and unique holdings (latest quarter).
      </p>

      <div className="mb-8 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {investorOptions.map((inv) => {
          const checked = selected.includes(inv.slug);
          const disabled = !checked && selected.length >= MAX_COMPARE;
          return (
            <label
              key={inv.slug}
              className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
                checked ? "border-blue-500 bg-blue-50" : "border-gray-200 bg-white"
              } ${disabled ? "opacity-50" : ""}`}
            >
              <input
                type="checkbox"
                checked={checked}
                disabled={disabled}
                onChange={() => toggle(inv.slug)}
              />
              <span className="truncate font-medium">{inv.name}</span>
            </label>
          );
        })}
      </div>

      {selected.length < 2 && (
        <p className="text-sm text-gray-400">Select at least two investors to compare.</p>
      )}

      {isLoading && <p className="text-sm text-gray-500">Loading comparison…</p>}
      {error && <p className="text-sm text-red-600">{(error as Error).message}</p>}

      {comparison && (
        <div className="space-y-8">
          <section>
            <h2 className="mb-3 text-lg font-semibold">Shared holdings</h2>
            {(comparison.overlap as { ticker?: string; name?: string }[])?.length ? (
              <ul className="grid gap-2 sm:grid-cols-2">
                {(comparison.overlap as { ticker?: string; name?: string }[]).map((s, i) => (
                  <li key={i} className="rounded border bg-white px-3 py-2 text-sm">
                    <span className="font-medium">{s.ticker}</span>
                    <span className="text-gray-500"> — {s.name}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">No overlapping positions in the latest quarter.</p>
            )}
          </section>

          <section>
            <h2 className="mb-3 text-lg font-semibold">Unique to each</h2>
            <div className="grid gap-4 md:grid-cols-2">
              {(
                comparison.investors as { id: number; slug: string; name: string }[] | undefined
              )?.map((inv) => {
                const unique =
                  (comparison.unique_to_each as Record<string, { ticker?: string; name?: string }[]>)?.[
                    String(inv.id)
                  ] ?? [];
                return (
                  <div key={inv.slug} className="rounded-lg border bg-white p-4">
                    <h3 className="mb-2 font-medium">{inv.name}</h3>
                    {unique.length === 0 ? (
                      <p className="text-xs text-gray-400">No unique positions</p>
                    ) : (
                      <ul className="max-h-48 space-y-1 overflow-y-auto text-sm text-gray-600">
                        {unique.slice(0, 20).map((s, i) => (
                          <li key={i}>
                            {s.ticker} — {s.name}
                          </li>
                        ))}
                        {unique.length > 20 && (
                          <li className="text-xs text-gray-400">+{unique.length - 20} more</li>
                        )}
                      </ul>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
