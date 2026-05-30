import type { SecurityBrief } from "@/types/holding";

const CUSIP_PATTERN = /^[A-Z0-9]{9}$/i;

/** True when we only have a CUSIP placeholder, not a resolved ticker. */
export function isUnresolvedSecurity(
  security: Pick<SecurityBrief, "ticker" | "name" | "exchange">
): boolean {
  if (security.exchange === "UNKNOWN") return true;
  if (security.name.startsWith("Unknown")) return true;
  return CUSIP_PATTERN.test(security.ticker.trim());
}

function cusipFromSecurity(security: Pick<SecurityBrief, "ticker" | "name">): string | null {
  const fromName = security.name.match(/^Unknown \(([^)]+)\)$/);
  if (fromName) return fromName[1];
  if (CUSIP_PATTERN.test(security.ticker)) return security.ticker;
  return null;
}

/** Primary label in tables and charts — never a raw CUSIP when unresolved. */
export function securityDisplayTitle(
  security: Pick<SecurityBrief, "ticker" | "name" | "exchange">
): string {
  if (!isUnresolvedSecurity(security)) return security.ticker;
  const cusip = cusipFromSecurity(security);
  if (security.name && !security.name.startsWith("Unknown")) {
    return security.name;
  }
  return cusip ? "Pending symbol lookup" : "Unidentified security";
}

/** Secondary line under the title. */
export function securityDisplaySubtitle(
  security: Pick<SecurityBrief, "ticker" | "name" | "exchange">
): string {
  if (!isUnresolvedSecurity(security)) return security.name;
  const cusip = cusipFromSecurity(security);
  return cusip ? `CUSIP ${cusip}` : security.name;
}

/** Pie chart / compact labels. */
export function securityChartLabel(
  security: Pick<SecurityBrief, "ticker" | "name" | "exchange">
): string {
  if (!isUnresolvedSecurity(security)) return security.ticker;
  const title = securityDisplayTitle(security);
  return title.length > 18 ? `${title.slice(0, 16)}…` : title;
}
