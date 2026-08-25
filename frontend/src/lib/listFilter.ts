import type { Region, Skill } from "../types";

export interface FilterableFields {
  name: string;
  address?: string;
  regions: Region[];
  skills: Skill[];
}

export interface FilterOptions {
  regions: Region[];
  skills: Skill[];
}

export function collectFilterOptions<T>(
  items: T[],
  extract: (item: T) => FilterableFields
): FilterOptions {
  const regionMap = new Map<number, Region>();
  const skillMap = new Map<number, Skill>();

  for (const item of items) {
    const { regions, skills } = extract(item);
    for (const region of regions) regionMap.set(region.id, region);
    for (const skill of skills) skillMap.set(skill.id, skill);
  }

  return {
    regions: Array.from(regionMap.values()).sort((a, b) => a.name.localeCompare(b.name)),
    skills: Array.from(skillMap.values()).sort((a, b) => a.name.localeCompare(b.name)),
  };
}

export function filterItems<T>(
  items: T[],
  extract: (item: T) => FilterableFields,
  search: string,
  selectedRegionIds: number[],
  selectedSkillIds: number[]
): T[] {
  const query = search.trim().toLowerCase();

  return items.filter((item) => {
    const { name, address, regions, skills } = extract(item);

    if (query) {
      const haystack = `${name} ${address ?? ""}`.toLowerCase();
      if (!haystack.includes(query)) return false;
    }

    if (selectedRegionIds.length > 0 && !regions.some((r) => selectedRegionIds.includes(r.id))) {
      return false;
    }

    if (selectedSkillIds.length > 0 && !skills.some((s) => selectedSkillIds.includes(s.id))) {
      return false;
    }

    return true;
  });
}
