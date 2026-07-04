import { useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Products from "./pages/Products";
import Forecast from "./pages/Forecast";
import Inventory from "./pages/Inventory";
import StockOut from "./pages/StockOut";
import Reorder from "./pages/Reorder";

const nav = [
  { to: "/", label: "Dashboard", icon: "◳", end: true },
  { to: "/products", label: "Products", icon: "🛒" },
  { to: "/forecast", label: "Demand Forecast", icon: "📈" },
  { to: "/inventory", label: "Inventory", icon: "📦" },
  { to: "/stockout", label: "Stock-Out Risk", icon: "⚠" },
  { to: "/reorder", label: "Reorder", icon: "🔁" },
];

export default function App() {
  const [dark, setDark] = useState(
    () => localStorage.getItem("theme") === "dark"
  );

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  return (
    <div className="flex h-screen overflow-hidden text-mac-ink dark:text-white">
      {/* Sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col gap-2 border-r border-mac-border bg-white/40 p-4 backdrop-blur-2xl dark:border-white/10 dark:bg-white/5 md:flex">
        <div className="px-1 pb-4 pt-2">
          <div className="text-sm font-semibold">SupplyChain&nbsp;IQ</div>
          <div className="text-xs text-mac-sub">Forecasting Platform</div>
        </div>
        <nav className="flex flex-col gap-1">
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                  isActive
                    ? "bg-mac-blue text-white shadow-soft"
                    : "text-mac-ink hover:bg-black/5 dark:text-white/80 dark:hover:bg-white/10"
                }`
              }
            >
              <span className="w-5 text-center">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto px-1">
          <button
            onClick={() => setDark((d) => !d)}
            className="w-full rounded-xl border border-mac-border bg-white/60 px-3 py-2 text-sm transition hover:bg-white dark:border-white/10 dark:bg-white/5"
          >
            {dark ? "☀ Light" : "🌙 Dark"} mode
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-5 py-6 md:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/products" element={<Products />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/stockout" element={<StockOut />} />
            <Route path="/reorder" element={<Reorder />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
