import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Compare Investors — PortfolioTracker",
  description: "Compare holdings overlap across top US institutional investors.",
};

export default function CompareLayout({ children }: { children: React.ReactNode }) {
  return children;
}
