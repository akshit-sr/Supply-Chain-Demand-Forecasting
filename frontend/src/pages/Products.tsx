import { useEffect, useState } from "react";
import { api, Product } from "../lib/api";
import { Card, Field, PageTitle, Spinner } from "../components/ui";

const PAGE_SIZE = 50;

export default function Products() {
  const [items, setItems] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("");
  const [departments, setDepartments] = useState<string[]>([]);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.departments().then(setDepartments);
  }, []);

  // Reset to first page when filters change.
  useEffect(() => {
    setPage(0);
  }, [search, department]);

  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => {
      api
        .products({
          search: search || undefined,
          department: department || undefined,
          limit: PAGE_SIZE,
          offset: page * PAGE_SIZE,
        })
        .then((r) => {
          setItems(r.items);
          setTotal(r.total);
        })
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(t);
  }, [search, department, page]);

  const pages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="flex flex-col gap-5">
      <PageTitle
        title="Products"
        subtitle={`${total.toLocaleString()} products in the catalog`}
      />

      <Card className="flex flex-col gap-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="sm:col-span-2">
            <Field label="Search product or brand">
              <input
                className="input"
                placeholder="e.g. milk, banana, Great Value…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </Field>
          </div>
          <Field label="Department">
            <select className="input" value={department} onChange={(e) => setDepartment(e.target.value)}>
              <option value="">All departments</option>
              {departments.map((d) => (
                <option key={d}>{d}</option>
              ))}
            </select>
          </Field>
        </div>
      </Card>

      <Card className="overflow-hidden p-0">
        {loading ? (
          <Spinner />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-mac-border text-left text-xs uppercase tracking-wide text-mac-sub dark:border-white/10">
                <tr>
                  <th className="px-4 py-3">Product</th>
                  <th className="px-4 py-3">Department</th>
                  <th className="px-4 py-3 text-right">Lot size</th>
                  <th className="px-4 py-3 text-right">Retail</th>
                  <th className="px-4 py-3 text-right">Current</th>
                  <th className="px-4 py-3 text-right">Discount</th>
                </tr>
              </thead>
              <tbody>
                {items.map((p) => (
                  <tr
                    key={p.sku}
                    className="border-b border-mac-border/60 transition hover:bg-black/[0.02] dark:border-white/5 dark:hover:bg-white/5"
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium">{p.product_name}</div>
                      <div className="text-xs text-mac-sub">
                        {p.brand} · SKU {p.sku}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div>{p.department}</div>
                      <div className="text-xs text-mac-sub">{p.category}</div>
                    </td>
                    <td className="px-4 py-3 text-right">{p.lot_size}</td>
                    <td className="px-4 py-3 text-right text-mac-sub">
                      {p.discount_pct > 0 ? (
                        <span className="line-through">${p.price_retail.toFixed(2)}</span>
                      ) : (
                        `$${p.price_retail.toFixed(2)}`
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-medium">
                      ${p.price_current.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {p.discount_pct > 0 ? (
                        <span className="pill bg-mac-green/15 text-mac-green">
                          -{p.discount_pct.toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-mac-sub">—</span>
                      )}
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-mac-sub">
                      No products match your filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {pages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-mac-sub">
            Page {page + 1} of {pages.toLocaleString()}
          </span>
          <div className="flex gap-2">
            <button
              className="rounded-xl border border-mac-border bg-white/60 px-3 py-1.5 disabled:opacity-40 dark:border-white/10 dark:bg-white/5"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              ← Prev
            </button>
            <button
              className="rounded-xl border border-mac-border bg-white/60 px-3 py-1.5 disabled:opacity-40 dark:border-white/10 dark:bg-white/5"
              disabled={page >= pages - 1}
              onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
