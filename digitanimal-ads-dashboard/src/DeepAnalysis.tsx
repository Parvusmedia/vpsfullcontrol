import { useMemo, useState } from "react";
import { countryFromBrief, num, truncEur } from "./lib/metrics";

export type Insight = {
  id: string;
  severity: "high" | "medium" | "low" | "info";
  entity: string;
  campaign: string;
  label: string;
  spend: number;
  clicks: number;
  conversions: number;
  cpa: number | null;
  action: string;
  detail: string;
};

export type DeepAnalysis = {
  window: { from: string; to: string };
  scope: string;
  active_campaign_count: number;
  insights: Insight[];
  ad_groups: Record<string, unknown>[];
  keywords: Record<string, unknown>[];
  ads: Record<string, unknown>[];
  pmax_notes: { campaign: string; note: string }[];
};

type View = "insights" | "ad_groups" | "keywords" | "ads";

const ENTITY_LABEL: Record<string, string> = {
  keyword: "Keyword",
  ad_group: "Grupo",
  ad: "Anuncio",
  campaign: "Campaña",
};

export function DeepAnalysisPanel({ data }: { data: DeepAnalysis }) {
  const [view, setView] = useState<View>("insights");
  const [filter, setFilter] = useState("ALL");

  const campaigns = useMemo(() => {
    const s = new Set<string>();
    data.insights.forEach((i) => s.add(i.campaign));
    return Array.from(s).sort();
  }, [data.insights]);

  const filteredInsights = data.insights.filter((i) => {
    if (filter === "ALL") return true;
    return countryFromBrief(i.campaign) === filter;
  });

  return (
    <div className="deep">
      <p className="deep-scope">
        {data.scope} · Ventana {data.window.from} → {data.window.to} ·{" "}
        <strong>{data.active_campaign_count}</strong> campañas
      </p>
      {data.pmax_notes.length > 0 && (
        <ul className="pmax-notes">
          {data.pmax_notes.map((p) => (
            <li key={p.campaign}>
              <code>{p.campaign}</code>: {p.note}
            </li>
          ))}
        </ul>
      )}
      <nav className="tabs inner">
        <button
          type="button"
          className={view === "insights" ? "active" : ""}
          onClick={() => setView("insights")}
        >
          Acciones prioritarias ({data.insights.length})
        </button>
        <button
          type="button"
          className={view === "ad_groups" ? "active" : ""}
          onClick={() => setView("ad_groups")}
        >
          Grupos ({data.ad_groups.length})
        </button>
        <button
          type="button"
          className={view === "keywords" ? "active" : ""}
          onClick={() => setView("keywords")}
        >
          Keywords ({data.keywords.length})
        </button>
        <button
          type="button"
          className={view === "ads" ? "active" : ""}
          onClick={() => setView("ads")}
        >
          Anuncios ({data.ads.length})
        </button>
      </nav>
      {view === "insights" && (
        <>
          <nav className="filters">
            <button
              type="button"
              className={filter === "ALL" ? "active" : ""}
              onClick={() => setFilter("ALL")}
            >
              Todos
            </button>
            {campaigns.map((c) => (
              <button
                key={c}
                type="button"
                className={filter === countryFromBrief(c) ? "active" : ""}
                onClick={() => setFilter(countryFromBrief(c))}
              >
                {countryFromBrief(c)}
              </button>
            ))}
          </nav>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Prior.</th>
                  <th>Nivel</th>
                  <th>Campaña</th>
                  <th>Elemento</th>
                  <th>Spend</th>
                  <th>Conv</th>
                  <th>CPA</th>
                  <th>Acción sugerida</th>
                </tr>
              </thead>
              <tbody>
                {filteredInsights.map((i) => (
                  <tr key={i.id} className={`sev-${i.severity}`}>
                    <td>{i.severity}</td>
                    <td>{ENTITY_LABEL[i.entity] ?? i.entity}</td>
                    <td title={i.campaign}>
                      <code className="platform-name">{i.campaign}</code>
                    </td>
                    <td title={i.detail}>{i.label}</td>
                    <td>{truncEur(i.spend).toFixed(2)}</td>
                    <td>{i.conversions > 0 ? i.conversions.toFixed(2) : "—"}</td>
                    <td>{i.cpa != null ? i.cpa.toFixed(2) : "—"}</td>
                    <td className="rec action-cell">
                      <span className="action-main">{i.action}</span>
                      {i.detail ? <span className="action-detail">{i.detail}</span> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {view === "ad_groups" && <EntityTable rows={data.ad_groups} />}
      {view === "keywords" && <EntityTable rows={data.keywords} />}
      {view === "ads" && <EntityTable rows={data.ads} />}
    </div>
  );
}

function EntityTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows.length) return <p className="empty">Sin datos en ventana (solo ENABLED).</p>;
  const keys = Array.from(
    rows.reduce((s, r) => {
      Object.keys(r).forEach((k) => s.add(k));
      return s;
    }, new Set<string>())
  );
  return (
    <div className="table-wrap">
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
    </div>
  );
}

function formatCell(v: unknown): string {
  if (v == null || v === "") return "—";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(2);
  const s = String(v);
  return s.length > 60 ? `${s.slice(0, 57)}…` : s;
}
