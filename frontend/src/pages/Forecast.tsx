import { useEffect, useState } from "react";
import {
  Area,
  ComposedChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, ForecastResult, Series } from "../lib/api";
import { Card, Field, PageTitle, Spinner } from "../components/ui";
import { SeriesSelector } from "../components/SeriesSelector";
import { tooltipStyle } from "./Dashboard";

export default function Forecast() {
  const [series, setSeries] = useState<Series[]>([]);
  const [sid, setSid] = useState("");
  const [horizon, setHorizon] = useState(28);
  const [result, setResult] = useState<ForecastResult>();
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
      .forecast(sid, horizon)
      .then(setResult)
      .finally(() => setLoading(false));
  }, [sid, horizon]);

  // Merge history + forecast onto a single timeline for the chart.
  const data = result
    ? [
        ...result.history.map((h) => ({
          date: h.date,
          actual: h.actual,
        })),
        ...result.forecast.map((f) => ({
          date: f.date,
          mean: f.mean,
          band: [f.lower, f.upper] as [number, number],
        })),
      ]
    : [];

  return (
    <div className="flex flex-col gap-5">
      <PageTitle
        title="Demand Forecast"
        subtitle="Multi-step demand prediction with confidence bands"
      />

      <Card className="flex flex-col gap-4">
        <SeriesSelector series={series} value={sid} onChange={setSid} />
        <Field label={`Forecast horizon: ${horizon} days`}>
          <input
            type="range"
            min={7}
            max={90}
            step={1}
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            className="accent-mac-blue"
          />
        </Field>
      </Card>

      <Card>
        <div className="mb-3 flex items-center justify-between">
          <div className="text-sm font-semibold">Actual vs Forecast</div>
          {result && (
            <span className="pill bg-mac-blue/15 text-mac-blue">model: {result.model}</span>
          )}
        </div>
        {loading || !result ? (
          <Spinner />
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(120,120,120,0.15)" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={40} />
              <YAxis tick={{ fontSize: 11 }} width={48} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area
                dataKey="band"
                stroke="none"
                fill="#0a84ff"
                fillOpacity={0.12}
                name="confidence"
              />
              <Line
                dataKey="actual"
                stroke="#1d1d1f"
                strokeWidth={2}
                dot={false}
                name="actual"
              />
              <Line
                dataKey="mean"
                stroke="#0a84ff"
                strokeWidth={2.5}
                dot={false}
                name="forecast"
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </Card>
    </div>
  );
}
