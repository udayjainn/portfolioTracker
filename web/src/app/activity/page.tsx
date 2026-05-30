"use client";

import { useState } from "react";
import { CountryTabs } from "@/components/home/CountryTabs";
import { RecentActivity } from "@/components/home/RecentActivity";

export default function ActivityPage() {
  const [country, setCountry] = useState<string | undefined>("US");

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="mb-2 text-2xl font-bold text-gray-900">Portfolio Activity</h1>
      <p className="mb-6 text-sm text-gray-500">
        Recent buys, sells, and position changes from SEC 13F filings.
      </p>
      <div className="mb-6">
        <CountryTabs selected={country} onChange={setCountry} />
      </div>
      <RecentActivity country={country} limit={50} />
    </div>
  );
}
