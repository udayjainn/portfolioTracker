import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Securities — PortfolioTracker",
  description: "Browse securities held by tracked US institutional investors.",
};

export default function SecuritiesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
