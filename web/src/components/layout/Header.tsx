"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAutocomplete } from "@/hooks/useSearch";

export function Header() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const { data } = useAutocomplete(query);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      setShowSuggestions(false);
    }
  }

  function handleSuggestionClick(suggestion: string) {
    setQuery(suggestion);
    setShowSuggestions(false);
    router.push(`/search?q=${encodeURIComponent(suggestion)}`);
  }

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <Link href="/" className="text-xl font-bold text-gray-900">
          PortfolioTracker
        </Link>

        <form onSubmit={handleSearch} className="relative mx-8 hidden flex-1 max-w-md md:block">
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder="Search investors, stocks..."
            className="w-full rounded-lg border border-gray-300 bg-gray-50 px-4 py-2 text-sm focus:border-blue-500 focus:bg-white focus:outline-none"
          />
          {showSuggestions && data?.suggestions && data.suggestions.length > 0 && (
            <div className="absolute top-full mt-1 w-full rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
              {data.suggestions.map((s) => (
                <button
                  key={s}
                  type="button"
                  onMouseDown={() => handleSuggestionClick(s)}
                  className="block w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </form>

        <nav className="flex items-center gap-6 text-sm">
          <Link href="/investors" className="text-gray-600 hover:text-gray-900">
            Investors
          </Link>
          <Link href="/securities" className="text-gray-600 hover:text-gray-900">
            Securities
          </Link>
          <Link href="/activity" className="text-gray-600 hover:text-gray-900">
            Activity
          </Link>
          <Link href="/compare" className="text-gray-600 hover:text-gray-900">
            Compare
          </Link>
          <Link href="/search" className="text-gray-600 hover:text-gray-900">
            Search
          </Link>
        </nav>
      </div>
    </header>
  );
}
