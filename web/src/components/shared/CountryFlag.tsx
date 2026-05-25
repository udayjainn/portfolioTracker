import { COUNTRIES } from "@/lib/constants";

export function CountryFlag({ code, showName = false }: { code: string; showName?: boolean }) {
  const country = COUNTRIES.find((c) => c.code === code);
  if (!country) return <span>{code}</span>;

  return (
    <span className="inline-flex items-center gap-1">
      <span>{country.flag}</span>
      {showName && <span>{country.name}</span>}
    </span>
  );
}
