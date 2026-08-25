import type { Region, Skill } from "../types";

interface Option {
  id: number;
  name: string;
}

interface ListFilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder: string;
  regionOptions: Region[];
  selectedRegionIds: number[];
  onRegionIdsChange: (ids: number[]) => void;
  skillOptions: Skill[];
  selectedSkillIds: number[];
  onSkillIdsChange: (ids: number[]) => void;
}

export function ListFilterBar({
  search,
  onSearchChange,
  searchPlaceholder,
  regionOptions,
  selectedRegionIds,
  onRegionIdsChange,
  skillOptions,
  selectedSkillIds,
  onSkillIdsChange,
}: ListFilterBarProps) {
  return (
    <div className="mb-3 flex flex-wrap gap-2">
      <input
        type="text"
        value={search}
        onChange={(event) => onSearchChange(event.target.value)}
        placeholder={searchPlaceholder}
        className="flex-1 min-w-[140px] text-sm border border-slate-300 rounded-md px-2 py-1"
      />
      <MultiSelectFilter
        label="Region"
        options={regionOptions}
        selectedIds={selectedRegionIds}
        onChange={onRegionIdsChange}
      />
      <MultiSelectFilter
        label="Skill"
        options={skillOptions}
        selectedIds={selectedSkillIds}
        onChange={onSkillIdsChange}
      />
    </div>
  );
}

interface MultiSelectFilterProps {
  label: string;
  options: Option[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
}

function MultiSelectFilter({ label, options, selectedIds, onChange }: MultiSelectFilterProps) {
  function toggle(id: number) {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((selectedId) => selectedId !== id));
    } else {
      onChange([...selectedIds, id]);
    }
  }

  return (
    <details className="relative">
      <summary className="list-none cursor-pointer text-sm border border-slate-300 rounded-md px-2 py-1 text-slate-600 select-none">
        {label}
        {selectedIds.length > 0 ? ` (${selectedIds.length})` : ""}
      </summary>
      {options.length > 0 && (
        <div className="absolute z-20 mt-1 min-w-[160px] max-h-48 overflow-y-auto bg-white border border-slate-200 rounded-md shadow-md p-2 space-y-1">
          {options.map((option) => (
            <label
              key={option.id}
              className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedIds.includes(option.id)}
                onChange={() => toggle(option.id)}
              />
              {option.name}
            </label>
          ))}
        </div>
      )}
    </details>
  );
}
