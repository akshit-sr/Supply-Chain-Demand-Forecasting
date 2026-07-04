import { useEffect, useState } from "react";
import { api, InventoryResult, Series } from "../lib/api";
import { Card, Field, PageTitle, Spinner, Stat } from "../components/ui";
import { SeriesSelector } from "../components/SeriesSelector";

export default function Inventory() {
  const [series, setSeries] = useState<Series[]>([]);
  const [sid, setSid] = useState("");
  const [leadTime, setLeadTime] = useState(7);
  const [serviceLevel, setServiceLevel] = useState(0.95);
  const [orderCost, setOrderCost] = useState(100);
  const [holdingCost, setHoldingCost] = useState(2);
  const [res, setRes] = useState<InventoryResult>();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.series().then((s) => {
      setSeries(s);
      setSid(s[0]?.series_id ?? "");
    });
  }, []);

  useEffect(() => {
    if (!sid) return;
    setLoading(true);
    api
      .inventory({
        series_id: sid,
        lead_time_days: leadTime,
        service_level: serviceLevel,
        order_cost: orderCost,
        holding_cost: holdingCost,
      })
      .then(setRes)
      .finally(() => setLoading(false));
  }, [sid, leadTime, serviceLevel, orderCost, holdingCost]);

  return (
    <div className="flex flex-col gap-5">
      <PageTitle
        title="Inventory Optimization"
        subtitle="EOQ, safety stock & reorder point derived from the demand forecast"
      />

      <Card className="flex flex-col gap-4">
        <SeriesSelector series={series} value={sid} onChange={setSid} />
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
          <Field label="Order cost ($)">
            <input
              type="number"
              className="input"
              value={orderCost}
              min={0}
              onChange={(e) => setOrderCost(Number(e.target.value))}
            />
          </Field>
          <Field label="Holding cost ($/unit/yr)">
            <input
              type="number"
              className="input"
              value={holdingCost}
              min={0.1}
              step={0.1}
              onChange={(e) => setHoldingCost(Number(e.target.value))}
            />
          </Field>
        </div>
      </Card>

      {loading || !res ? (
        <Spinner />
      ) : (
        <>
          <Card className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <div className="font-medium">{res.product_name}</div>
              <div className="text-xs text-mac-sub">
                {res.brand} · {res.department} · Location {res.location}
              </div>
            </div>
            <div className="flex gap-4 text-sm">
              <span className="text-mac-sub">
                Unit price <span className="font-medium text-mac-ink dark:text-white">${res.unit_price.toFixed(2)}</span>
              </span>
              <span className="text-mac-sub">
                Lot size <span className="font-medium text-mac-ink dark:text-white">{res.lot_size}</span>
              </span>
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Stat
              label="Reorder Point"
              value={Math.round(res.reorder_point).toLocaleString()}
              sub="reorder when stock hits this"
              accent="blue"
            />
            <Stat
              label="Safety Stock"
              value={Math.round(res.safety_stock).toLocaleString()}
              sub={`extra buffer to stay in stock ${(res.inputs.service_level * 100).toFixed(0)}% of the time`}
              accent="orange"
            />
            <Stat
              label="Economic Order Qty"
              value={Math.round(res.economic_order_qty).toLocaleString()}
              sub="optimal lot size (EOQ)"
              accent="green"
            />
            <Stat
              label="Order-up-to Level"
              value={Math.round(res.order_up_to_level).toLocaleString()}
              sub="periodic review target"
              accent="purple"
            />
          </div>

          <Card>
            <div className="mb-3 text-sm font-semibold">Demand & Cost Breakdown</div>
            <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
              <Row k="Annual demand" v={res.annual_demand} />
              <Row k="Demand over lead time" v={res.demand_over_lead_time} />
              <Row k="Est. annual ordering cost" v={res.estimated_annual_ordering_cost} money />
              <Row k="Est. annual holding cost" v={res.estimated_annual_holding_cost} money />
              <Row
                k="Est. total annual cost"
                v={res.estimated_total_annual_cost}
                money
                bold
              />
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function Row({
  k,
  v,
  money,
  bold,
}: {
  k: string;
  v: number;
  money?: boolean;
  bold?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between rounded-xl bg-black/[0.03] px-3 py-2 dark:bg-white/5 ${
        bold ? "font-semibold" : ""
      }`}
    >
      <span className="text-mac-sub">{k}</span>
      <span>
        {money ? "$" : ""}
        {v.toLocaleString()}
      </span>
    </div>
  );
}
