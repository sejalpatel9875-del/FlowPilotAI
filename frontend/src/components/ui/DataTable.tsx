import React from "react";
import { cn } from "@/utils/cn";
import { EmptyState } from "./EmptyState";
import { Skeleton } from "./Skeleton";

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  onRowClick?: (item: T) => void;
  className?: string;
}

export function DataTable<T extends { id?: string | number }>({
  columns,
  data,
  isLoading = false,
  emptyTitle = "No records found",
  emptyDescription = "There are currently no items to display.",
  onRowClick,
  className,
}: DataTableProps<T>) {
  if (isLoading) {
    return (
      <div className="space-y-3 p-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
      />
    );
  }

  return (
    <div className={cn("w-full overflow-x-auto rounded-xl border border-border/70 glass-panel", className)}>
      <table className="w-full text-left text-xs">
        <thead className="bg-muted/50 text-muted-foreground uppercase tracking-wider font-semibold border-b border-border/80">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className={cn("px-4 py-3 font-medium", col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border/40 text-foreground">
          {data.map((item, idx) => (
            <tr
              key={item.id ?? idx}
              onClick={() => onRowClick?.(item)}
              className={cn(
                "transition-colors hover:bg-card-hover/80",
                onRowClick && "cursor-pointer"
              )}
            >
              {columns.map((col) => (
                <td key={col.key} className={cn("px-4 py-3 whitespace-nowrap", col.className)}>
                  {col.render ? col.render(item) : (item as any)[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
