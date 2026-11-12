import { useEffect, useMemo, useState } from "react";
import { countryFromBrief, num, pctDisplay, truncEur, type Row } from "./lib/metrics";
import { normalizeCumplimientoRow } from "./lib/normalize";
import { recommend, type Recommendation } from "./lib/recommendations";
import "./app.css";

type Payload = {
  source?: string;
  message?: string;
  updatedAt?: string;
  cumplimiento?: Row[];
  presupuesto_activacion?: Row[];
  agent_cambios?: Row[];
};

type Tab = "cumplimiento" | "cambios" | "presupuesto";

export default function App() {
  const [data, setData] = useState<Payload | null>(null);
  const [filter, setFilter] = useState<string>("ALL");
  const [tab, setTab] = useState<Tab>("cumplimiento");
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/dashboard")
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData({ source: "error", message: "No API" }));
  }, []);

  const rows = useMemo(
    () => (data?.cumplimiento ?? []).map(normalizeCumplimientoRow),
    [data?.cumplimiento]
  );

  const enriched = useMemo(
    () =>
      rows.map((r) => ({
        row: r,
        rec: recommend(r),
        key: String(r.nombre_en_brief ?? r.campana ?? ""),
      })),
    [rows]
  );

  const countries = useMemo(() => {
    const s = new Set<string>();
    enriched.forEach(({ row }) => {
      const k = String(row.nombre_en_brief ?? "");
      if (k) s.add(countryFromBrief(k));
    });
    return Array.from(s).sort();
  }, [enriched]);

  const filtered = enriched.filter(({ row }) => {
    if (filter === "ALL") return true;
    return countryFromBrief(String(row.nombre_en_brief ?? "")) === filter;
  });

  const totals = useMemo(() => {
    let spend = 0;
    let budget = 0;
    filtered.forEach(({ row }) => {
      spend += num(row.spend);
      budget += num(row.budget_consumido);
    });
    return { spend: truncEur(spend), budget: truncEur(budget), pct: budget > 0 ? (spend / budget) * 100 : 0 };
  }, [filtered]);

  const alerts = filtered.filter(({ rec }) => rec.severity === "alert" || rec.severity === "warn").length;

  const isSample = data?.source === "sample" || data?.source === "error";
  const cambios = data?.agent_cambios ?? [];
  const presupuesto = data?.presupuesto_activacion ?? [];

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
          <span className="label">Spend acumulado</span>
          <span className="value">{totals.spend.toFixed(2)} €</span>
        </div>
        <div className="kpi">
          <span className="label">Budget consumido (plan)</span>
          <span className="value">{totals.budget.toFixed(2)} €</span>
        </div>
        <div className="kpi">
          <span className="label">Ritmo global</span>
          <span className="value">{totals.pct.toFixed(1)} %</span>
        </div>
        <div className="kpi">
          <span className="label">Campañas con aviso</span>
          <span className="value">{alerts}</span>
        </div>
      </section>

      <nav className="tabs">
        <button type="button" className={tab === "cumplimiento" ? "active" : ""} onClick={() => setTab("cumplimiento")}>
          Cumplimiento + recomendaciones
        </button>
        <button type="button" className={tab === "cambios" ? "active" : ""} onClick={() => setTab("cambios")}>
          Cambios agente ({cambios.length})
        </button>
        <button type="button" className={tab === "presupuesto" ? "active" : ""} onClick={() => setTab("presupuesto")}>
          Presupuesto activación
        </button>
      </nav>

      {tab === "cumplimiento" && (
        <>
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

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th></th>
                  <th>País</th>
                  <th>Campaña</th>
                  <th>€/día</th>
                  <th>Spend €</th>
                  <th>Budget plan €</th>
                  <th>Ritmo %</th>
                  <th>Desvío €</th>
                  <th>Tier</th>
                  <th>Recomendación</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(({ row, rec, key }) => (
                  <CampaignRows
                    key={key}
                    row={row}
                    rec={rec}
                    open={expanded === key}
                    onToggle={() => setExpanded(expanded === key ? null : key)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === "cambios" && (
        <div className="table-wrap">
          {cambios.length === 0 ? (
            <p className="empty">
              Sin filas en <code>agent_cambios</code>. Crea la pestaña en la hoja (ver doc agent_cambios) y vuelve a
              implementar el Apps Script con la versión nueva del repo.
            </p>
          ) : (
            <DynamicTable rows={cambios} />
          )}
        </div>
      )}

      {tab === "presupuesto" && (
        <div className="table-wrap">
          <DynamicTable rows={presupuesto} />
        </div>
      )}
    </div>
  );
}

function CampaignRows({
  row,
  rec,
  open,
  onToggle,
}: {
  row: Row;
  rec: Recommendation;
  open: boolean;
  onToggle: () => void;
}) {
  const brief = String(row.nombre_en_brief ?? "");
  const campana = String(row.campana ?? brief);
  const spend = truncEur(num(row.spend));
  const bud = truncEur(num(row.budget_consumido));
  const daily = truncEur(num(row.presupuesto_diario));
  const pct = pctDisplay(row.pct_cumplimiento);
  const desvio = truncEur(num(row.desvio_eur));
  const low = pct < 80;
  const high = pct > 120;

  return (
    <>
      <tr className={low ? "low" : high ? "high" : ""} data-severity={rec.severity}>
        <td>
          <button type="button" className="expand" onClick={onToggle} aria-expanded={open}>
            {open ? "−" : "+"}
          </button>
        </td>
        <td>{countryFromBrief(brief)}</td>
        <td title={brief}>{campana}</td>
        <td>{daily.toFixed(2)}</td>
        <td>{spend.toFixed(2)}</td>
        <td>{bud.toFixed(2)}</td>
        <td>
          <motionBar pct={Math.min(pct, 120)} warn={low} />
          <span className="pct-text">{pct.toFixed(1)} %</span>
        </td>
        <td>{desvio.toFixed(2)}</td>
        <td title={rec.review}>{rec.tier}</td>
        <td className={`rec rec-${rec.severity}`}>{rec.text}</td>
      </tr>
      {open && (
        <tr className="detail">
          <td colSpan={10}>
            <DetailGrid row={row} rec={rec} />
          </td>
        </tr>
      )}
    </>
  );
}

function DetailGrid({ row, rec }: { row: Row; rec: Recommendation }) {
  const skip = new Set(["nombre_en_brief", "campana"]);
  const entries = Object.entries(row).filter(([k]) => !skip.has(k));
  return (
    <div className="detail-grid">
      <div>
        <strong>Brief</strong>
        <code>{String(row.nombre_en_brief)}</code>
      </div>
      <div>
        <strong>Cadencia</strong>
        <span>{rec.review}</span>
      </div>
      <div className="detail-fields">
        {entries.map(([k, v]) => (
          <div key={k}>
            <span className="field-key">{k}</span>
            <span className="field-val">{formatCell(v)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatCell(v: unknown): string {
  if (v == null || v === "") return "—";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(2);
  if (typeof v === "string" && /^\d{4}-\d{2}-\d{2}/.test(v)) {
    try {
      return new Date(v).toLocaleDateString("es-ES");
    } catch {
      return v;
    }
  }
  return String(v);
}

function DynamicTable({ rows }: { rows: Row[] }) {
  if (!rows.length) return <p className="empty">Sin datos.</p>;
  const keys = Array.from(
    rows.reduce((s, r) => {
      Object.keys(r).forEach((k) => s.add(k));
      return s;
    }, new Set<string>())
  );
  return (
    <table>
      <thead>
        <tr>
          {keys.map((k) => (
            <th key={k}>{k}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            {keys.map((k) => (
              <td key={k}>{formatCell(r[k])}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function motionBar({ pct, warn }: { pct: number; warn?: boolean }) {
  return (
    <div className="bar-track">
      <div className={`bar-fill${warn ? " warn" : ""}`} style={{ width: `${Math.min(pct, 100)}%` }} />
    </div>
  );
}
