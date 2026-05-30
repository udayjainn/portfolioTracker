"use client";

import { COUNTRIES } from "@/lib/constants";

export function CountryTabs({
  selected,
  onChange,
}: {
  selected: string | undefined;
  onChange: (country: string | undefined) => void;
}) {
  return (
    <div className="flex gap-2">
      <button
        onClick={() => onChange(undefined)}
        className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
          !selected ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
        }`}
      >
        All
      </button>
      {COUNTRIES.map((c) => {
        const live = c.code === "US";
        return (
          <button
            key={c.code}
            type="button"
            disabled={!live}
            onClick={() => live && onChange(c.code)}
            title={live ? undefined : "Coming soon"}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
              selected === c.code
                ? "bg-blue-600 text-white"
                : live
                  ? "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  : "cursor-not-allowed bg-gray-50 text-gray-400"
            }`}
          >
            {c.flag} {c.name}
            {!live && <span className="ml-1 text-xs">(soon)</span>}
          </button>
        );
      })}
    </div>
  );
}
