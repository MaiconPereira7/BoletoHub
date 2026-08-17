import type { Category } from "@/types"

export function CategoryBadge({ category }: { category: Category | null }) {
  if (!category) {
    return <span className="text-muted-foreground">—</span>
  }

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-transparent px-2.5 py-0.5 text-xs font-semibold"
      style={{ backgroundColor: `${category.color}20`, color: category.color }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: category.color }} />
      {category.name}
    </span>
  )
}
