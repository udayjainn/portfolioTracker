import { api } from "@/lib/api";
import { InvestorDetailClient } from "./InvestorDetailClient";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const investor = await api.getInvestor(slug);
    return {
      title: `${investor.name} — Portfolio | PortfolioTracker`,
      description: `View ${investor.name}'s complete portfolio holdings, recent changes, and investment history.`,
    };
  } catch {
    return { title: "Investor Not Found | PortfolioTracker" };
  }
}

export default async function InvestorPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <InvestorDetailClient slug={slug} />;
}
