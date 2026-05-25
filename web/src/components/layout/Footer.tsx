import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          <div>
            <h3 className="font-semibold text-gray-900">PortfolioTracker</h3>
            <p className="mt-2 text-sm text-gray-500">
              Track celebrity and institutional investor portfolios across the globe.
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">Explore</h4>
            <ul className="mt-2 space-y-1 text-sm">
              <li><Link href="/investors" className="text-gray-500 hover:text-gray-700">Investors</Link></li>
              <li><Link href="/search" className="text-gray-500 hover:text-gray-700">Search</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">Data Sources</h4>
            <ul className="mt-2 space-y-1 text-sm text-gray-500">
              <li>SEC EDGAR (USA)</li>
              <li>SEDI (Canada)</li>
              <li>Companies House (UK)</li>
              <li>BSE / NSE (India)</li>
            </ul>
          </div>
        </div>
        <div className="mt-8 border-t border-gray-200 pt-4 text-center text-xs text-gray-400">
          Data is sourced from public regulatory filings. Not financial advice.
        </div>
      </div>
    </footer>
  );
}
