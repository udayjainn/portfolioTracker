"use client";

import { useInvestor, useInvestorHoldings } from "@/hooks/useInvestor";
import { formatCurrency, formatDate } from "@/lib/formatters";
import {
  investorDisplaySubtitle,
  investorDisplayTitle,
  investorTypeLabel,
} from "@/lib/investorDisplay";
import { CountryFlag } from "@/components/shared/CountryFlag";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { HoldingsTable } from "@/components/investor/HoldingsTable";
import { PortfolioPieChart } from "@/components/investor/PortfolioPieChart";

export function InvestorDetailClient({ slug }: { slug: string }) {
  const { data: investor, isLoading } = useInvestor(slug);
  const { data: holdingsData } = useInvestorHoldings(slug, { limit: 25, sort: "-value_usd" });

  if (isLoading) return <LoadingSpinner className="py-20" />;
  if (!investor) return <p className="py-20 text-center text-gray-500">Investor not found.</p>;

  const hasPortfolioData =
    investor.latest_filing_date != null && (investor.positions_count ?? 0) > 0;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-bold text-gray-900">{investorDisplayTitle(investor)}</h1>
          <span className="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">
            {investorTypeLabel(investor.investor_type)}
          </span>
          <CountryFlag code={investor.country} />
        </div>
        <p className="mt-1 text-gray-500">{investorDisplaySubtitle(investor)}</p>
      </div>

      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Portfolio Value" value={formatCurrency(investor.total_holdings_value)} />
        <StatCard label="Holdings" value={String(investor.positions_count ?? "—")} />
        <StatCard label="Country" value={investor.country} />
        <StatCard label="Last Updated" value={formatDate(investor.latest_filing_date)} />
      </div>

      {!hasPortfolioData ? (
        <EmptyState
          title="Portfolio not available yet"
          description="This investor is tracked, but no 13F filing has been ingested yet. Check back after the pipeline processes their latest SEC filing."
        />
      ) : (
        <div className="mb-10 grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Allocation</h2>
            {holdingsData?.data?.length ? (
              <PortfolioPieChart holdings={holdingsData.data} />
            ) : (
              <p className="text-sm text-gray-500">Loading allocation…</p>
            )}
          </div>
          <div className="lg:col-span-2">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Holdings</h2>
            <HoldingsTable slug={slug} />
          </div>
        </div>
      )}
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
