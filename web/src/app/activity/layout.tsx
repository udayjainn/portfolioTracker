import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Portfolio Activity — PortfolioTracker",
  description: "Recent institutional portfolio changes from SEC 13F filings.",
};

export default function ActivityLayout({ children }: { children: React.ReactNode }) {
  return children;
}
