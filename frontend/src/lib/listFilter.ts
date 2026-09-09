import type { Product, Region } from "../types";

export interface FilterableFields {
  name: string;
  address?: string;
  regions: Region[];
  products: Product[];
}

export interface FilterOptions {
  regions: Region[];
  products: Product[];
}

export function collectFilterOptions<T>(
  items: T[],
  extract: (item: T) => FilterableFields
): FilterOptions {
  const regionMap = new Map<number, Region>();
  const productMap = new Map<number, Product>();

  for (const item of items) {
    const { regions, products } = extract(item);
    for (const region of regions) regionMap.set(region.id, region);
    for (const product of products) productMap.set(product.id, product);
  }

  return {
    regions: Array.from(regionMap.values()).sort((a, b) => a.name.localeCompare(b.name)),
    products: Array.from(productMap.values()).sort((a, b) => a.number.localeCompare(b.number)),
  };
}

export function filterItems<T>(
  items: T[],
  extract: (item: T) => FilterableFields,
  search: string,
  selectedRegionIds: number[],
  selectedProductIds: number[]
): T[] {
  const query = search.trim().toLowerCase();

  return items.filter((item) => {
    const { name, address, regions, products } = extract(item);

    if (query) {
      const haystack = `${name} ${address ?? ""}`.toLowerCase();
      if (!haystack.includes(query)) return false;
    }

    if (selectedRegionIds.length > 0 && !regions.some((r) => selectedRegionIds.includes(r.id))) {
      return false;
    }

    if (
      selectedProductIds.length > 0 &&
      !products.some((p) => selectedProductIds.includes(p.id))
    ) {
      return false;
    }

    return true;
  });
}
