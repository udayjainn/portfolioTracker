import type { InvestorSummary } from "@/types/investor";

/** Human-readable labels aligned with DB `investor_type` (LLD). */
export const INVESTOR_TYPE_LABELS: Record<string, string> = {
  INDIVIDUAL: "Investor",
  INSTITUTIONAL: "Institution",
};

export function investorTypeLabel(type: string): string {
  return INVESTOR_TYPE_LABELS[type] ?? type;
}

/** Card/detail title: person name vs firm name for institutions. */
export function investorDisplayTitle(investor: Pick<InvestorSummary, "name" | "firm_name" | "investor_type">): string {
  if (investor.investor_type === "INSTITUTIONAL") {
    return investor.firm_name || investor.name;
  }
  return investor.name;
}

export function investorDisplaySubtitle(
  investor: Pick<InvestorSummary, "name" | "firm_name" | "investor_type">
): string {
  if (investor.investor_type === "INSTITUTIONAL") {
    return "Asset manager · 13F filer";
  }
  return investor.firm_name || "Fund manager · 13F filer";
}
