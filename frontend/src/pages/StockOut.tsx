import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, ForecastResult, Series, StockoutResult } from "../lib/api";
import { Badge, Card, Field, PageTitle, Spinner, Stat } from "../components/ui";
import { SeriesSelector } from "../components/SeriesSelector";
import { tooltipStyle } from "./Dashboard";

const RISK_COLOR: Record<string, string> = {
  low: "#30d158",
  medium: "#ff9f0a",
  high: "#ff453a",
  critical: "#ff453a",
};

export default function StockOut() {
  const [series, setSeries] = useState<Series[]>([]);
  const [sid, setSid] = useState("");
  const [onHand, setOnHand] = useState(1000);
  const [leadTime, setLeadTime] = useState(7);
  const [res, setRes] = useState<StockoutResult>();
  const [forecast, setForecast] = useState<ForecastResult>();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.series().then((s) => {
      setSeries(s);
      const first = s[0];
      setSid(first?.series_id ?? "");
      if (first) setOnHand(Math.round(first.avg_daily_demand * 10));
    });
  }, []);

  useEffect(() => {
    if (!sid) return;
    setLoading(true);
    Promise.all([
      api.stockout({ series_id: sid, on_hand: onHand, lead_time_days: leadTime }),
      api.forecast(sid, 45),
    ])
      .then(([s, f]) => {
        setRes(s);
        setForecast(f);
      })
      .finally(() => setLoading(false));
  }, [sid, onHand, leadTime]);

  const pct = res ? Math.round(res.stockout_probability * 100) : 0;
  const gauge = [
    { name: "risk", value: pct },
    { name: "safe", value: 100 - pct },
  ];

  // Projected inventory: on-hand drawn down each day by the forecasted demand.
  let remaining = onHand;
  const depletion =
    forecast?.forecast.map((f) => {
      remaining = remaining - f.mean;
      return { date: f.date, remaining: Math.round(remaining) };
    }) ?? [];

  return (
    <div className="flex flex-col gap-5">
      <PageTitle
        title="Stock-Out Prediction"
        subtitle="Probability of running out before replenishment arrives"
      />

      <Card className="flex flex-col gap-4">
        <SeriesSelector series={series} value={sid} onChange={setSid} />
        <div className="grid grid-cols-2 gap-3">
          <Field label="On-hand inventory (units)">
            <input
              type="number"
              className="input"
              value={onHand}
              min={0}
              onChange={(e) => setOnHand(Number(e.target.value))}
            />
          </Field>
          <Field label="Lead time (days)">
            <input
              type="number"
              className="input"
              value={leadTime}
              min={1}
              onChange={(e) => setLeadTime(Number(e.target.value))}
            />
          </Field>
        </div>
      </Card>

      {loading || !res ? (
        <Spinner />
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Card className="flex flex-col items-center justify-center">
            <div className="relative">
              <ResponsiveContainer width={200} height={200}>
                <PieChart>
                  <Pie
                    data={gauge}
                    dataKey="value"
                    innerRadius={70}
                    outerRadius={90}
                    startAngle={90}
                    endAngle={-270}
                    stroke="none"
                  >
                    <Cell fill={RISK_COLOR[res.risk_level]} />
                    <Cell fill="rgba(120,120,120,0.15)" />
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-3xl font-semibold ${res.risk_level === 'critical' ? 'text-mac-red animate-pulse-glow shadow-glow rounded-full px-2' : ''}`}>{pct}%</span>
                <span className="text-xs text-mac-sub">stock-out risk</span>
              </div>
            </div>
            <div className="mt-2">
              <Badge kind={res.risk_level} />
            </div>
          </Card>

          <div className="lg:col-span-2 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Stat
              label="Days Until Stock-Out"
              value={res.days_until_stockout ?? "Safe"}
              sub={res.projected_stockout_date ?? "covered by current stock"}
              accent={res.covered_by_current_stock ? "green" : "red"}
            />
            <Stat
              label="Expected Demand (lead time)"
              value={Math.round(res.expected_demand_over_lead_time).toLocaleString()}
              accent="blue"
            />
            <Stat
              label="On Hand"
              value={Math.round(res.on_hand).toLocaleString()}
              sub="current inventory"
              accent="purple"
            />
            <Stat
              label="Coverage"
              value={res.covered_by_current_stock ? "✓ Sufficient" : "⚠ At Risk"}
              sub={`lead time ${res.lead_time_days}d`}
              accent={res.covered_by_current_stock ? "green" : "orange"}
            />
          </div>
        </div>
      )}

      {!loading && res && depletion.length > 0 && (
        <Card>
          <div className="mb-1 text-sm font-semibold">Projected Inventory Depletion</div>
          <div className="mb-3 text-xs text-mac-sub">
            On-hand stock drawn down by forecasted daily demand. The red line marks zero
            stock; the dashed line marks when replenishment would arrive (lead time).
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={depletion}>
              <defs>
                <linearGradient id="dep" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#0a84ff" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#0a84ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(120,120,120,0.15)" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={32} />
              <YAxis tick={{ fontSize: 11 }} width={52} />
              <Tooltip contentStyle={tooltipStyle} />
              <ReferenceLine y={0} stroke="#ff453a" strokeWidth={1.5} />
              {depletion[leadTime - 1] && (
                <ReferenceLine
                  x={depletion[leadTime - 1].date}
                  stroke="#8e8e93"
                  strokeDasharray="4 4"
                  label={{ value: "lead time", fontSize: 10, fill: "#8e8e93", position: "insideTopRight" }}
                />
              )}
              <Area
                type="monotone"
                dataKey="remaining"
                stroke="#0a84ff"
                strokeWidth={2.5}
                fill="url(#dep)"
                name="units remaining"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  );
}
