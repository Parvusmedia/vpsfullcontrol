import { useEffect, useMemo, useState } from "react";
import {
  ATTRIBUTED_CONV_TITLE,
  formatAttributedConversions,
  PURCHASE_COL_TITLE,
  REG_COL_TITLE,
} from "./lib/conversions-display";
import { countryFromBrief, num, pctDisplay, truncEur, type Row } from "./lib/metrics";
import { normalizeCumplimientoRow } from "./lib/normalize";
import { recommend, type Recommendation } from "./lib/recommendations";
import { DeepAnalysisPanel, type DeepAnalysis } from "./DeepAnalysis";
import "./app.css";

type Payload = {
  source?: string;
  _delivery?: string;
  snapshot_built_at?: string;
  message?: string;
  updatedAt?: string;
  metrics_note?: string;
  metrics_period?: { from: string; to: string };
  cumplimiento?: Row[];
  presupuesto_activacion?: Row[];
  agent_cambios?: Row[];
  analysis_window?: { from: string; to: string };
  deep_analysis?: DeepAnalysis | null;
};

type Tab = "cumplimiento" | "profundo" | "cambios" | "presupuesto";

export default function App() {
  const [data, setData] = useState<Payload | null>(null);
  const [filter, setFilter] = useState<string>("ALL");
  const [tab, setTab] = useState<Tab>("cumplimiento");
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    const parsePayload = (text: string): Payload | null => {
      try {
        return JSON.parse(text) as Payload;
      } catch {
        return null;
      }
    };

    const load = async () => {
      const host = window.location.hostname;
      if (host.endsWith(".apps.grok.bot")) {
        window.location.replace(`https://digitanimal-ads.pmediaplus.com${window.location.pathname}${window.location.search}`);
        return;
      }

      for (const url of ["/api/dashboard", "/dashboard.json"] as const) {
        try {
          const r = await fetch(url, { cache: "no-store" });
          const text = await r.text();
          const json = parsePayload(text);
          if (!json) continue;
          if (!r.ok) {
            if (url === "/dashboard.json") continue;
            setData({
              ...json,
              source: "error",
              message: json.message ?? `Error HTTP ${r.status}`,
            });
            return;
          }
          setData(
            url === "/dashboard.json"
              ? { ...json, _delivery: json._delivery ?? "build_snapshot" }
              : { ...json, _delivery: "api" }
          );
          return;
        } catch {
          /* try next URL */
        }
      }
      const onGrok = host.includes("grok.bot");
      setData({
        source: "error",
        message: onGrok
          ? "Estás en la URL antigua de Cursor Apps (sin API). Abre https://digitanimal-ads.pmediaplus.com"
          : `No hay datos en ${host}: ni /api/dashboard ni /dashboard.json respondieron JSON. Prueba en ventana privada o desactiva extensiones que bloqueen peticiones.`,
      });
    };

    void load();
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
  const isSnapshot = data?._delivery === "build_snapshot";
  const cambios = data?.agent_cambios ?? [];
  const presupuesto = data?.presupuesto_activacion ?? [];

  return (
    <div className="page">
      <header>
        <h1>Digitanimal · Google Ads</h1>
        <p className="meta">
          {isSample && <span className="badge warn">Muestra / Windsor API</span>}
          {!isSample && isSnapshot && (
            <span className="badge warn">Snapshot al publicar</span>
          )}
          {!isSample && !isSnapshot && <span className="badge ok">Windsor en vivo</span>}
          {(data?.snapshot_built_at || data?.updatedAt) && (
            <>
              {" "}
              · Actualizado{" "}
              {new Date(data.snapshot_built_at ?? data.updatedAt!).toLocaleString("es-ES")}
            </>
          )}
        </p>
      </header>

      {(data?.message || data?.metrics_note) && (
        <p className="banner">
          {[data.message, data.metrics_note].filter(Boolean).join(" · ")}
        </p>
      )}

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
        <button type="button" className={tab === "profundo" ? "active" : ""} onClick={() => setTab("profundo")}>
          Análisis profundo
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
            <table className="data-table">
              <thead>
                <tr>
                  <th className="col-num"></th>
                  <th className="col-num">País</th>
                  <th className="col-campaign">Campaña (Google Ads)</th>
                  <th className="col-num">€/día</th>
                  <th className="col-num">Spend €</th>
                  <th title={REG_COL_TITLE}>Reg. (atrib.)</th>
                  <th className="col-num" title={PURCHASE_COL_TITLE}>
                    Compra (atrib.)
                  </th>
                  <th className="col-num">CPL €</th>
                  <th className="col-num">CPA €</th>
                  <th className="col-num">Budget plan €</th>
                  <th className="col-num">Ritmo %</th>
                  <th className="col-num">Desvío €</th>
                  <th className="col-num">Tier</th>
                  <th className="col-rec">Recomendación</th>
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

      {tab === "profundo" && (
        <>
          {!data?.deep_analysis ? (
            <p className="empty">
              Análisis profundo requiere <code>WINDSOR_API_KEY</code> (grupos, keywords, anuncios ENABLED).
            </p>
          ) : (
            <DeepAnalysisPanel data={data.deep_analysis} />
          )}
        </>
      )}

      {tab === "cambios" && (
        <div className="table-wrap">
          {cambios.length === 0 ? (
            <p className="empty">
              Historial de cambios: agente <code>digitanimal-google-ads</code> (JSONL). Próximo: sincronizar aquí vía
              Windsor o API del agente.
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
  const aliasBrief = String(row.campana_brief ?? "");
  const spend = truncEur(num(row.spend));
  const convLead = num(row.conversions_lead);
  const convPurchase = num(row.conversions_purchase);
  const cpl =
    row.cpl != null && row.cpl !== ""
      ? truncEur(num(row.cpl))
      : convLead > 0
        ? truncEur(spend / convLead)
        : null;
  const cpa =
    row.cpa != null && row.cpa !== ""
      ? truncEur(num(row.cpa))
      : convPurchase > 0
        ? truncEur(spend / convPurchase)
        : null;
  const convOther = num(row.conversions_other);
  const convTip =
    convOther > 0
      ? ` · otras conv. (micro): ${convOther.toFixed(2)}`
      : "";
  const costTitle = `${ATTRIBUTED_CONV_TITLE}${convTip}`;
  const purchaseActions = row.conversion_purchase_actions as
    | { name: string; conversions: number }[]
    | undefined;
  const purchaseTip =
    purchaseActions && purchaseActions.length > 0
      ? `\nAcciones compra: ${purchaseActions.map((a) => `${a.name} (${Number(a.conversions).toFixed(2)})`).join("; ")}`
      : "";
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
        <td className="col-num">{countryFromBrief(brief)}</td>
        <td className="col-campaign" title={aliasBrief ? `Alias brief: ${aliasBrief}` : brief}>
          {campana}
        </td>
        <td className="col-num">{daily.toFixed(2)}</td>
        <td className="col-num">{spend.toFixed(2)}</td>
        <td title={costTitle}>{formatAttributedConversions(convLead)}</td>
        <td title={`${costTitle}${purchaseTip}`}>
          {formatAttributedConversions(convPurchase)}
        </td>
        <td className="col-num" title={costTitle}>
          {cpl != null ? cpl.toFixed(2) : "—"}
        </td>
        <td className="col-num" title={costTitle}>
          {cpa != null ? cpa.toFixed(2) : "—"}
        </td>
        <td className="col-num">{bud.toFixed(2)}</td>
        <td>
          <MotionBar pct={Math.min(pct, 120)} warn={low} />
          <span className="pct-text">{pct.toFixed(1)} %</span>
        </td>
        <td className="col-num">{desvio.toFixed(2)}</td>
        <td className="col-num" title={rec.review}>
          {rec.tier}
        </td>
        <td className={`rec col-rec rec-${rec.severity}`}>{rec.text}</td>
      </tr>
      {open && (
        <tr className="detail">
          <td colSpan={14}>
            <DetailGrid row={row} rec={rec} />
          </td>
        </tr>
      )}
    </>
  );
}

function DetailGrid({ row, rec }: { row: Row; rec: Recommendation }) {
  const skip = new Set([
    "nombre_en_brief",
    "campana",
    "conversion_purchase_actions",
    "conversion_lead_actions",
    "conversion_attribution_note",
  ]);
  const entries = Object.entries(row).filter(([k]) => !skip.has(k));
  const purchaseActions = row.conversion_purchase_actions as
    | { name: string; conversions: number }[]
    | undefined;
  const leadActions = row.conversion_lead_actions as
    | { name: string; conversions: number }[]
    | undefined;
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
      {(purchaseActions?.length || leadActions?.length) ? (
        <div className="detail-conv-actions">
          <strong>Acciones de conversión (Windsor)</strong>
          {leadActions && leadActions.length > 0 ? (
            <ul>
              {leadActions.map((a) => (
                <li key={`l-${a.name}`}>
                  <span className="tag">Registro</span> {a.name}:{" "}
                  {formatAttributedConversions(Number(a.conversions))}
                </li>
              ))}
            </ul>
          ) : null}
          {purchaseActions && purchaseActions.length > 0 ? (
            <ul>
              {purchaseActions.map((a) => (
                <li key={`p-${a.name}`}>
                  <span className="tag">Compra</span> {a.name}:{" "}
                  {formatAttributedConversions(Number(a.conversions))}
                </li>
              ))}
            </ul>
          ) : null}
          <p className="muted-note">{String(row.conversion_attribution_note ?? ATTRIBUTED_CONV_TITLE)}</p>
        </div>
      ) : null}
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

function MotionBar({ pct, warn }: { pct: number; warn?: boolean }) {
  return (
    <div className="bar-track">
      <div className={`bar-fill${warn ? " warn" : ""}`} style={{ width: `${Math.min(pct, 100)}%` }} />
    </div>
  );
}
