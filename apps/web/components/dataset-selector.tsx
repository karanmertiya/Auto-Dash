"use client";

import { useEffect, useState } from "react";
import { Database } from "lucide-react";

import { Dataset, apiGet } from "@/lib/api";

export function DatasetSelector({ onSelect }: { onSelect?: (dataset: Dataset) => void }) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selected, setSelected] = useState("");

  useEffect(() => {
    apiGet<Dataset[]>("/api/datasets").then((items) => {
      setDatasets(items);
      const stored = window.localStorage.getItem("dashforge.datasetId");
      const current = items.find((item) => item.id === stored) ?? items[0];
      if (current) {
        setSelected(current.id);
        window.localStorage.setItem("dashforge.datasetId", current.id);
        onSelect?.(current);
      }
    }).catch(() => setDatasets([]));
  }, [onSelect]);

  return (
    <label className="flex items-center gap-2 text-sm">
      <Database className="h-4 w-4 text-zinc-500" />
      <select
        className="focus-ring rounded border-line bg-white text-sm"
        value={selected}
        onChange={(event) => {
          const dataset = datasets.find((item) => item.id === event.target.value);
          setSelected(event.target.value);
          if (dataset) {
            window.localStorage.setItem("dashforge.datasetId", dataset.id);
            onSelect?.(dataset);
          }
        }}
      >
        {datasets.length === 0 ? <option>No datasets yet</option> : null}
        {datasets.map((dataset) => (
          <option key={dataset.id} value={dataset.id}>
            {dataset.name}
          </option>
        ))}
      </select>
    </label>
  );
}

