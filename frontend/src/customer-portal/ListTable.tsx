import type { ReactNode } from "react";

interface Column<T> {
  header: string;
  render: (item: T) => ReactNode;
}

interface ListTableProps<T> {
  items: T[];
  columns: Column<T>[];
  getKey: (item: T) => number | string;
  onSelect: (item: T) => void;
  emptyMessage: string;
}

export function ListTable<T>({
  items,
  columns,
  getKey,
  onSelect,
  emptyMessage,
}: ListTableProps<T>) {
  if (items.length === 0) {
    return <p className="text-sm text-slate-500">{emptyMessage}</p>;
  }

  return (
    <table className="w-full text-sm border-collapse">
      <thead>
        <tr className="text-left text-slate-500 border-b border-slate-200">
          {columns.map((column) => (
            <th key={column.header} className="py-2 pr-4 font-medium">
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr
            key={getKey(item)}
            onClick={() => onSelect(item)}
            className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer"
          >
            {columns.map((column) => (
              <td key={column.header} className="py-2 pr-4 text-slate-700">
                {column.render(item)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
