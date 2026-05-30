"use client";

import { useState } from "react";
import { CountryTabs } from "@/components/home/CountryTabs";
import { InvestorGrid } from "@/components/investor/InvestorGrid";
import { InvestorTypeTabs } from "@/components/investor/InvestorTypeTabs";
import { SORT_OPTIONS } from "@/lib/constants";

export default function InvestorsPage() {
  const [country, setCountry] = useState<string | undefined>("US");
  const [type, setType] = useState<string | undefined>(undefined);
  const [sort, setSort] = useState("-total_value_usd");

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold text-gray-900">13F Filers</h1>
      <p className="mb-6 text-sm text-gray-500">
        <span className="font-medium text-blue-800">Investors</span> are named fund managers;
        {" "}
        <span className="font-medium text-violet-800">Institutions</span> are asset managers and
        large firms filing as themselves.
      </p>

      <div className="mb-6 flex flex-wrap items-center gap-4">
        <CountryTabs selected={country} onChange={setCountry} />
      </div>

      <div className="mb-4">
        <InvestorTypeTabs selected={type} onChange={setType} />
      </div>

      <div className="mb-6 flex justify-end">
        <label className="flex items-center gap-2 text-sm text-gray-600">
          Sort by
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="rounded-md border px-3 py-2 text-sm text-gray-900"
          >
            {SORT_OPTIONS.investors.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </label>
      </div>

      <InvestorGrid country={country} type={type} sort={sort} />
    </div>
  );
}
