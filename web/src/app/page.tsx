"use client";

import { useState } from "react";
import { CountryTabs } from "@/components/home/CountryTabs";
import { TrendingInvestors } from "@/components/home/TrendingInvestors";
import { MostBoughtSold } from "@/components/home/MostBoughtSold";
import { RecentActivity } from "@/components/home/RecentActivity";

export default function Home() {
  const [country, setCountry] = useState<string | undefined>(undefined);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <section className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900">
          Track the World&apos;s Top Investors
        </h1>
        <p className="mt-2 text-gray-500">
          Follow portfolio moves of celebrity investors, hedge funds, and institutions across the globe.
        </p>
      </section>

      <div className="mb-8">
        <CountryTabs selected={country} onChange={setCountry} />
      </div>

      <section className="mb-10">
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Trending Investors</h2>
        <TrendingInvestors country={country} />
      </section>

      <section className="mb-10">
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Market Moves</h2>
        <MostBoughtSold country={country} />
      </section>

      <section>
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Recent Activity</h2>
        <RecentActivity country={country} />
      </section>
    </div>
  );
}
