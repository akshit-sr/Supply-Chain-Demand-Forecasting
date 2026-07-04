import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, Kpis } from "../lib/api";
import { Card, PageTitle, Spinner, Stat } from "../components/ui";

export default function Dashboard() {
  const [kpis, setKpis] = useState<Kpis>();
  const [trend, setTrend] = useState<{ date: string; demand: number }[]>([]);
  const [err, setErr] = useState<string>();

  useEffect(() => {
    Promise.all([api.kpis(), api.trend(180)])
      .then(([k, t]) => {
        setKpis(k);
        setTrend(t);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  if (err)
    return (
      <Card className="text-mac-red">
        Failed to reach the API. Is the backend running and the model trained?
        <div className="mt-1 text-xs text-mac-sub">{err}</div>
      </Card>
    );
  if (!kpis) return <Spinner />;

  return (
    <div className="flex flex-col gap-5">
      <PageTitle
        title="Supply Chain Overview"
        subtitle={`${kpis.total_products_catalog.toLocaleString()} products in catalog · ${kpis.modeled_series} modeled product-location series`}
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat
          label="Units Sold (30d)"
          value={kpis.demand_last_30d.toLocaleString()}
          sub={
            <span className={kpis.demand_growth_30d_pct >= 0 ? "text-mac-green" : "text-mac-red"}>
              {kpis.demand_growth_30d_pct >= 0 ? "▲" : "▼"}{" "}
              {Math.abs(kpis.demand_growth_30d_pct)}% vs prev 30d
            </span>
          }
          accent="blue"
        />
        <Stat
          label="Catalog Products"
          value={kpis.total_products_catalog.toLocaleString()}
          sub={`${kpis.modeled_departments} departments`}
          accent="green"
        />
        <Stat
          label="Modeled Items"
          value={kpis.modeled_series}
          sub={`${kpis.modeled_locations} locations`}
          accent="purple"
        />
        <Stat
          label="Model Skill"
          value={kpis.model_skill_pct != null ? `+${kpis.model_skill_pct}%` : "—"}
          sub={kpis.model ? `${kpis.model} · WAPE ${kpis.model_wape} · vs baseline` : "train model"}
          accent="orange"
        />
      </div>

      <Card>
        <div className="mb-3 text-sm font-semibold">Total Daily Units Sold · last 180 days</div>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={trend}>
            <defs>
              <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0a84ff" stopOpacity={0.4} />
                <stop offset="100%" stopColor="#0a84ff" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(120,120,120,0.15)" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={40} />
            <YAxis tick={{ fontSize: 11 }} width={48} />
            <Tooltip contentStyle={tooltipStyle} />
            <Area
              type="monotone"
              dataKey="demand"
              stroke="#0a84ff"
              strokeWidth={2}
              fill="url(#g)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

export const tooltipStyle = {
  borderRadius: 12,
  border: "1px solid rgba(0,0,0,0.08)",
  background: "rgba(255,255,255,0.9)",
  backdropFilter: "blur(8px)",
  fontSize: 12,
};
