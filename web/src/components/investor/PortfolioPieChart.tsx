"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import type { HoldingSummary } from "@/types/holding";
import { formatCurrency, formatPercent } from "@/lib/formatters";

const COLORS = ["#2563eb", "#7c3aed", "#db2777", "#ea580c", "#16a34a", "#0891b2", "#4f46e5", "#be123c"];

export function PortfolioPieChart({ holdings }: { holdings: HoldingSummary[] }) {
  const top = holdings.slice(0, 8);
  const rest = holdings.slice(8);
  const restPct = rest.reduce((sum, h) => sum + h.pct_of_portfolio, 0);

  const chartData = [
    ...top.map((h) => ({ name: h.security.ticker, value: h.pct_of_portfolio, usd: h.value_usd })),
    ...(rest.length > 0 ? [{ name: "Other", value: restPct, usd: rest.reduce((s, h) => s + h.value_usd, 0) }] : []),
  ];

  if (!chartData.length) return null;

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name }) => name}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number, _: string, props: { payload: { usd: number } }) => [
              `${formatPercent(value)} (${formatCurrency(props.payload.usd)})`,
              "Allocation",
            ]}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
