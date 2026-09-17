import type { Region } from "../types";

export interface FilterOption {
  id: number;
  name: string;
}

export interface FilterableFields {
  name: string;
  address?: string;
  regions: Region[];
  secondary: FilterOption[];
}

export interface FilterOptions {
  regions: Region[];
  secondary: FilterOption[];
}

export function collectFilterOptions<T>(
  items: T[],
  extract: (item: T) => FilterableFields
): FilterOptions {
  const regionMap = new Map<number, Region>();
  const secondaryMap = new Map<number, FilterOption>();

  for (const item of items) {
    const { regions, secondary } = extract(item);
    for (const region of regions) regionMap.set(region.id, region);
    for (const option of secondary) secondaryMap.set(option.id, option);
  }

  return {
    regions: Array.from(regionMap.values()).sort((a, b) => a.name.localeCompare(b.name)),
    secondary: Array.from(secondaryMap.values()).sort((a, b) => a.name.localeCompare(b.name)),
  };
}

export function filterItems<T>(
  items: T[],
  extract: (item: T) => FilterableFields,
  search: string,
  selectedRegionIds: number[],
  selectedSecondaryIds: number[]
): T[] {
  const query = search.trim().toLowerCase();

  return items.filter((item) => {
    const { name, address, regions, secondary } = extract(item);

    if (query) {
      const haystack = `${name} ${address ?? ""}`.toLowerCase();
      if (!haystack.includes(query)) return false;
    }

    if (selectedRegionIds.length > 0 && !regions.some((r) => selectedRegionIds.includes(r.id))) {
      return false;
    }

    if (
      selectedSecondaryIds.length > 0 &&
      !secondary.some((s) => selectedSecondaryIds.includes(s.id))
    ) {
      return false;
    }

    return true;
  });
}
