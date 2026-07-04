import { useMemo } from "react";
import { Series } from "../lib/api";
import { Field } from "./ui";

// Selects a modeled product-location series via Product -> Location dropdowns.
export function SeriesSelector({
  series,
  value,
  onChange,
}: {
  series: Series[];
  value: string;
  onChange: (id: string) => void;
}) {
  const selected = series.find((s) => s.series_id === value);

  // Unique products (by sku) for the first dropdown.
  const products = useMemo(() => {
    const seen = new Map<string, Series>();
    for (const s of series) if (!seen.has(s.sku)) seen.set(s.sku, s);
    return [...seen.values()].sort((a, b) =>
      a.product_name.localeCompare(b.product_name)
    );
  }, [series]);

  const locations = useMemo(
    () =>
      series
        .filter((s) => s.sku === selected?.sku)
        .map((s) => s.location)
        .sort(),
    [series, selected?.sku]
  );

  function pickProduct(sku: string) {
    const match = series.find((s) => s.sku === sku);
    if (match) onChange(match.series_id);
  }
  function pickLocation(loc: string) {
    const match = series.find((s) => s.sku === selected?.sku && s.location === loc);
    if (match) onChange(match.series_id);
  }

  if (!selected) return null;

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      <div className="sm:col-span-2">
        <Field label="Product">
          <select className="input" value={selected.sku} onChange={(e) => pickProduct(e.target.value)}>
            {products.map((p) => (
              <option key={p.sku} value={p.sku}>
                {p.product_name} — {p.brand}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field label="Location">
        <select className="input" value={selected.location} onChange={(e) => pickLocation(e.target.value)}>
          {locations.map((l) => (
            <option key={l}>{l}</option>
          ))}
        </select>
      </Field>
    </div>
  );
}
