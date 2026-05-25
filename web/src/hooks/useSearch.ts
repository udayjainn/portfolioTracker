"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useDebounce } from "./useDebounce";

export function useSearch(query: string, type?: string) {
  const debouncedQuery = useDebounce(query, 300);

  return useQuery({
    queryKey: ["search", debouncedQuery, type],
    queryFn: () => api.search(debouncedQuery, type),
    enabled: debouncedQuery.length >= 2,
  });
}

export function useAutocomplete(query: string) {
  const debouncedQuery = useDebounce(query, 200);

  return useQuery({
    queryKey: ["autocomplete", debouncedQuery],
    queryFn: () => api.autocomplete(debouncedQuery),
    enabled: debouncedQuery.length >= 1,
  });
}
