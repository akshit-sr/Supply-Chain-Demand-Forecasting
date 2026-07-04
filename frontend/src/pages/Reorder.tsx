import { useEffect, useState } from "react";
import { api, ReorderRow } from "../lib/api";
import { Badge, Card, Field, PageTitle, Spinner } from "../components/ui";

type SortKey = "urgency" | "risk" | "order_qty" | "customer";

const URGENCY_RANK: Record<string, number> = { urgent: 0, soon: 1, ok: 2 };

export default function Reorder() {
  const [rows, setRows] = useState<ReorderRow[]>([]);
  const [leadTime, setLeadTime] = useState(7);
  const [serviceLevel, setServiceLevel] = useState(0.95);
  const [onHandDays, setOnHandDays] = useState(10);
  const [sortBy, setSortBy] = useState<SortKey>("urgency");
  const [loading, setLoading] = useState(true);
  const [ordered, setOrdered] = useState<Record<string, boolean>>({});
  const [ordering, setOrdering] = useState<string | null>(null);

  const handleOrder = async (series_id: string, qty: number) => {
    setOrdering(series_id);
    try {
      await api.placeOrder({ series_id, order_qty: qty });
      setOrdered(prev => ({ ...prev, [series_id]: true }));
    } catch (e) {
      alert("Failed to place order: " + e);
    } finally {
      setOrdering(null);
    }
  };

  // Auto-recompute when inputs change (debounced so typing doesn't spam the API).
  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => {
      api
        .reorderAll({
          lead_time_days: leadTime,
          service_level: serviceLevel,
          order_cost: 50,
          on_hand_days: onHandDays,
        })
        .then(setRows)
        .finally(() => setLoading(false));
    }, 350);
    return () => clearTimeout(t);
  }, [leadTime, serviceLevel, onHandDays]);

  const urgent = rows.filter((r) => r.urgency === "urgent").length;
  const soon = rows.filter((r) => r.urgency === "soon").length;

  const sortedRows = [...rows].sort((a, b) => {
    switch (sortBy) {
      case "risk":
        return b.stockout_probability - a.stockout_probability;
      case "order_qty":
        return b.recommended_order_qty - a.recommended_order_qty;
      case "customer":
        return a.product_name.localeCompare(b.product_name) || a.location.localeCompare(b.location);
      case "urgency":
      default:
        // Group strictly by urgency tier; within a tier, larger orders first.
        return (
          (URGENCY_RANK[a.urgency] ?? 3) - (URGENCY_RANK[b.urgency] ?? 3) ||
          b.recommended_order_qty - a.recommended_order_qty
        );
    }
  });

  return (
    <div className="flex flex-col gap-5">
      <PageTitle
        title="Reorder"
        subtitle="Forecast-driven reorder recommendations ranked by urgency"
      />

      <Card className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Field label="Lead time (days)">
            <input
              type="number"
              className="input"
              value={leadTime}
              min={1}
              onChange={(e) => setLeadTime(Number(e.target.value))}
            />
          </Field>
          <Field label="Service level">
            <select
              className="input"
              value={serviceLevel}
              onChange={(e) => setServiceLevel(Number(e.target.value))}
            >
              {[0.9, 0.95, 0.98, 0.99].map((v) => (
                <option key={v} value={v}>
                  {(v * 100).toFixed(0)}%
                </option>
              ))}
            </select>
          </Field>
          <Field label="Simulated stock (days)">
            <input
              type="number"
              className="input"
              value={onHandDays}
              min={0}
              onChange={(e) => setOnHandDays(Number(e.target.value))}
            />
          </Field>
          <Field label="Sort by">
            <select
              className="input"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortKey)}
            >
              <option value="urgency">Urgency</option>
              <option value="risk">Stock-out risk</option>
              <option value="order_qty">Order quantity</option>
              <option value="customer">Product name</option>
            </select>
          </Field>
        </div>
        <div className="flex gap-2 text-xs">
          <span className="pill bg-mac-red/15 text-mac-red">{urgent} urgent</span>
          <span className="pill bg-mac-orange/15 text-mac-orange">{soon} soon</span>
          <span className="pill bg-mac-green/15 text-mac-green">
            {rows.length - urgent - soon} ok
          </span>
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
                  <th className="px-4 py-3">Urgency</th>
                  <th className="px-4 py-3 text-right">Stock-out risk</th>
                  <th className="px-4 py-3 text-right">On hand</th>
                  <th className="px-4 py-3 text-right">Reorder pt</th>
                  <th className="px-4 py-3 text-right">Order qty</th>
                  <th className="px-4 py-3">Order by</th>
                  <th className="px-4 py-3">Action</th>
                </tr>
              </thead>
              <tbody>
                {sortedRows.map((r) => (
                  <tr
                    key={r.series_id}
                    className={`border-b border-mac-border/60 transition hover:bg-black/[0.02] dark:border-white/5 dark:hover:bg-white/5 ${r.urgency === 'urgent' ? 'animate-pulse-bg bg-mac-red/5' : ''}`}
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium">{r.product_name}</div>
                      <div className="text-xs text-mac-sub">
                        {r.brand} · {r.department} · Loc {r.location}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge kind={r.urgency} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      {Math.round(r.stockout_probability * 100)}%
                    </td>
                    <td className="px-4 py-3 text-right">{Math.round(r.on_hand).toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">
                      {Math.round(r.reorder_point).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right font-medium">
                      {r.should_reorder ? Math.round(r.recommended_order_qty).toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-3 text-xs text-mac-sub">
                      {r.recommended_order_date ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      {ordered[r.series_id] ? (
                        <span className="text-mac-green font-medium text-xs">✓ Ordered</span>
                      ) : r.should_reorder ? (
                        <button
                          onClick={() => handleOrder(r.series_id, r.recommended_order_qty)}
                          disabled={ordering === r.series_id}
                          className="btn py-1 px-2 text-xs w-24"
                        >
                          {ordering === r.series_id ? "Ordering..." : "Place Order"}
                        </button>
                      ) : (
                        <span className="text-mac-sub text-xs">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
