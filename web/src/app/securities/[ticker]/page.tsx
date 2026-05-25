import { api } from "@/lib/api";
import { SecurityDetailClient } from "./SecurityDetailClient";

export async function generateMetadata({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = await params;
  try {
    const security = await api.getSecurity(ticker);
    return {
      title: `${security.ticker} — ${security.name} | PortfolioTracker`,
      description: `See which institutional investors hold ${security.name} (${security.ticker}).`,
    };
  } catch {
    return { title: "Security Not Found | PortfolioTracker" };
  }
}

export default async function SecurityPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = await params;
  return <SecurityDetailClient ticker={ticker} />;
}
