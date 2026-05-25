"use client";

import { useState } from "react";
import { CountryTabs } from "@/components/home/CountryTabs";
import { InvestorGrid } from "@/components/investor/InvestorGrid";
import { INVESTOR_TYPES, SORT_OPTIONS } from "@/lib/constants";

export default function InvestorsPage() {
  const [country, setCountry] = useState<string | undefined>(undefined);
  const [type, setType] = useState<string | undefined>(undefined);
  const [sort, setSort] = useState("portfolio_value");

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">All Investors</h1>

      <div className="mb-6 flex flex-wrap items-center gap-4">
        <CountryTabs selected={country} onChange={setCountry} />
      </div>

      <div className="mb-6 flex gap-4">
        <select
          value={type ?? ""}
          onChange={(e) => setType(e.target.value || undefined)}
          className="rounded-md border px-3 py-2 text-sm"
        >
          <option value="">All Types</option>
          {INVESTOR_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="rounded-md border px-3 py-2 text-sm"
        >
          {SORT_OPTIONS.investors.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
      </div>

      <InvestorGrid country={country} type={type} sort={sort} />
    </div>
  );
}
