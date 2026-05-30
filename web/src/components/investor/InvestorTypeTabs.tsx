"use client";

import { INVESTOR_TYPES } from "@/lib/constants";

const ALL = { value: undefined as string | undefined, label: "All" };

export function InvestorTypeTabs({
  selected,
  onChange,
}: {
  selected?: string;
  onChange: (type: string | undefined) => void;
}) {
  const tabs = [ALL, ...INVESTOR_TYPES];

  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label="Investor category">
      {tabs.map((tab) => {
        const active = selected === tab.value;
        return (
          <button
            key={tab.label}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(tab.value)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition ${
              active
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
