"use client";

import { useEffect, useState } from "react";
import { getCategories } from "@/lib/api";
import type { CategoryCount } from "@/lib/types";

interface CategoryFilterProps {
  value: string;
  onChange: (category: string) => void;
}

export default function CategoryFilter({ value, onChange }: CategoryFilterProps) {
  const [categories, setCategories] = useState<CategoryCount[]>([]);

  useEffect(() => {
    let active = true;
    getCategories()
      .then((response) => {
        if (active) setCategories(response.categories);
      })
      .catch((error: unknown) => {
        console.error("Unable to load product categories:", error);
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <label className="flex items-center gap-3 text-sm font-medium">
      <span className="whitespace-nowrap">Category</span>
      <select
        className="min-w-0 rounded-full border border-ink/15 bg-white px-4 py-2.5 outline-none focus:border-moss"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">All categories</option>
        {categories.map(({ category, count }) => (
          <option key={category} value={category}>
            {category} ({count})
          </option>
        ))}
      </select>
    </label>
  );
}
