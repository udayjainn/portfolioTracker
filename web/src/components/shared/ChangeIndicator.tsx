import type { ChangeType } from "@/types/holding";
import { CHANGE_TYPE_CONFIG } from "@/lib/constants";

export function ChangeIndicator({ type }: { type: ChangeType }) {
  const config = CHANGE_TYPE_CONFIG[type];
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${config.bg} ${config.color}`}>
      {config.label}
    </span>
  );
}
