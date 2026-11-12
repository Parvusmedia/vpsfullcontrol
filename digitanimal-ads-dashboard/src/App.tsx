import { useEffect, useMemo, useState } from "react";
import { countryFromBrief, num, pctDisplay, truncEur, type Row } from "./lib/metrics";
import "./app.css";

type Payload = {
  source?: string;
  message?: string;
  updatedAt?: string;
  cumplimiento?: Row[];
};

export default function App() {
  const [data, setData] = useState<Payload | null>(null);
  const [filter, setFilter] = useState<string>("ALL");

  useEffect(() => {
    fetch("/api/dashboard")
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData({ source: "error", message: "No API" }));
  }, []);

  const rows = data?.cumplimiento ?? [];
  const countries = useMemo(() => {
    const s = new Set<string>();
    rows.forEach((r) => {
      const k = String(r.nombre_en_brief ?? "");
      if (k) s.add(countryFromBrief(k));
    });
    return Array.from(s).sort();
  }, [rows]);

  const filtered = rows.filter((r) => {
    if (filter === "ALL") return true;
    return countryFromBrief(String(r.nombre_en_brief ?? "")) === filter;
  });

  const totals = useMemo(() => {
    let spend = 0;
    let budget = 0;
    filtered.forEach((r) => {
      spend += num(r.spend);
      budget += num(r.budget_consumido);
    });
    return { spend: truncEur(spend), budget: truncEur(budget), pct: budget > 0 ? (spend / budget) * 100 : 0 };
  }, [filtered]);

  const isSample = data?.source === "sample" || data?.source === "error";

  return (
    <div className="page">
      <header>
        <h1>Digitanimal · Google Ads</h1>
        <p className="meta">
          {isSample && <span className="badge warn">Muestra / conectar hoja</span>}
          {!isSample && <span className="badge ok">En vivo</span>}
          {data?.updatedAt && <> · Actualizado {new Date(data.updatedAt).toLocaleString("es-ES")}</>}
        </p>
      </header>

      {data?.message && <p className="banner">{data.message}</p>}

      <section className="kpis">
        <div className="kpi">
          <span className="label">Spend</span>
          <span className="value">{totals.spend.toFixed(2)} €</span>
        </div>
        <div className="kpi">
          <span className="label">Budget consumido (plan)</span>
          <span className="value">{totals.budget.toFixed(2)} €</span>
        </div>
        <div className="kpi">
          <span className="label">Ritmo</span>
          <span className="value">{totals.pct.toFixed(1)} %</span>
        </div>
      </section>

      <nav className="filters">
        <button type="button" className={filter === "ALL" ? "active" : ""} onClick={() => setFilter("ALL")}>
          Todos
        </button>
        {countries.map((c) => (
          <button key={c} type="button" className={filter === c ? "active" : ""} onClick={() => setFilter(c)}>
            {c}
          </button>
        ))}
      </nav>

      <table>
        <thead>
          <tr>
            <th>País</th>
            <th>Campaña</th>
            <th>Spend €</th>
            <th>Budget plan €</th>
            <th>Ritmo %</th>
            <th>Desvío €</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((r, i) => {
            const brief = String(r.nombre_en_brief ?? "");
            const campana = String(r.campana ?? brief);
            const spend = truncEur(num(r.spend));
            const bud = truncEur(num(r.budget_consumido));
            const pct = pctDisplay(r.pct_cumplimiento);
            const desvio = truncEur(num(r.desvio_eur));
            const low = pct < 80;
            return (
              <tr key={brief || i} className={low ? "low" : ""}>
                <td>{countryFromBrief(brief)}</td>
                <td title={brief}>{campana}</td>
                <td>{spend.toFixed(2)}</td>
                <td>{bud.toFixed(2)}</td>
                <td>
                  <motionBar pct={Math.min(pct, 120)} />
                  <span className="pct-text">{pct.toFixed(1)} %</span>
                </td>
                <td>{desvio.toFixed(2)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function motionBar({ pct }: { pct: number }) {
  return (
    <div className="bar-track">
      <div className="bar-fill" style={{ width: `${Math.min(pct, 100)}%` }} />
    </div>
  );
}
