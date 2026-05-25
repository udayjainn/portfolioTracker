"use client";

import { useInvestor, useInvestorHoldings } from "@/hooks/useInvestor";
import { formatCurrency, formatDate } from "@/lib/formatters";
import { CountryFlag } from "@/components/shared/CountryFlag";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { HoldingsTable } from "@/components/investor/HoldingsTable";
import { PortfolioPieChart } from "@/components/investor/PortfolioPieChart";

export function InvestorDetailClient({ slug }: { slug: string }) {
  const { data: investor, isLoading } = useInvestor(slug);
  const { data: holdingsData } = useInvestorHoldings(slug, { limit: 25 });

  if (isLoading) return <LoadingSpinner className="py-20" />;
  if (!investor) return <p className="py-20 text-center text-gray-500">Investor not found.</p>;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-gray-900">{investor.name}</h1>
          <CountryFlag code={investor.country} />
        </div>
        <p className="mt-1 text-gray-500">{investor.investor_type}</p>
      </div>

      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Portfolio Value" value={formatCurrency(investor.portfolio_value_usd)} />
        <StatCard label="Holdings" value={String(investor.holdings_count)} />
        <StatCard label="Country" value={investor.country} />
        <StatCard label="Last Updated" value={formatDate(investor.last_report_date)} />
      </div>

      <div className="mb-10 grid grid-cols-1 gap-8 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Allocation</h2>
          {holdingsData?.data && <PortfolioPieChart holdings={holdingsData.data} />}
        </div>
        <div className="lg:col-span-2">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Holdings</h2>
          <HoldingsTable slug={slug} />
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <p className="text-xs text-gray-400">{label}</p>
      <p className="mt-1 text-xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
