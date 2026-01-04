import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import Chart from "react-apexcharts";

const API_BASE = "http://127.0.0.1:5000";

export default function App() {
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const [source, setSource] = useState("live");
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("symbol");
  const [sortDir, setSortDir] = useState("asc");

  const [autoRefresh, setAutoRefresh] = useState(false);
  const [onlyAnomalies, setOnlyAnomalies] = useState(false);

  const [selected, setSelected] = useState(null);
  const [timeframe, setTimeframe] = useState("1h");
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyErr, setHistoryErr] = useState("");
  const [candleSeries, setCandleSeries] = useState([{ data: [] }]);

  const [reportOpen, setReportOpen] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportErr, setReportErr] = useState("");
  const [report, setReport] = useState(null);
  const [showRawReport, setShowRawReport] = useState(false);

  const endpoint = source === "scraped" ? "/api/scraped-data" : "/api/live-data";

  const downloadFile = (content, filename, mime) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const exportJSON = () => {
    downloadFile(JSON.stringify(tokens, null, 2), "crypto_data.json", "application/json");
  };

  const exportCSV = () => {
    if (!tokens?.length) return;

    const headers = Object.keys(tokens[0]);
    const escape = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const rows = tokens.map((row) => headers.map((h) => escape(row[h])).join(","));
    const csv = [headers.join(","), ...rows].join("\n");

    downloadFile(csv, "crypto_data.csv", "text/csv;charset=utf-8;");
  };

  const exportReportJSON = () => {
    if (!report) return;
    downloadFile(JSON.stringify(report, null, 2), "analysis_report.json", "application/json");
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      setErr("");
      const res = await axios.get(`${API_BASE}${endpoint}`);
      setTokens(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      setErr(e?.message || "API error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setErr("");
        const res = await axios.get(`${API_BASE}${endpoint}`);
        if (!cancelled) setTokens(Array.isArray(res.data) ? res.data : []);
      } catch (e) {
        if (!cancelled) setErr(e?.message || "API error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [endpoint]);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(() => fetchData(), 30000);
    return () => clearInterval(id);
  }, [autoRefresh, endpoint]);

  const filteredSorted = useMemo(() => {
    const q = searchTerm.trim().toUpperCase();

    let arr = tokens;
    if (q) arr = arr.filter((t) => String(t.symbol || "").toUpperCase().includes(q));

    const toNum = (v) => {
      const n = Number(v);
      return Number.isFinite(n) ? n : 0;
    };

    const sorted = [...arr].sort((a, b) => {
      if (sortBy === "price") {
        const ap = toNum(a.current_price ?? a.price ?? a.lastPrice ?? a.close);
        const bp = toNum(b.current_price ?? b.price ?? b.lastPrice ?? b.close);
        return ap - bp;
      }
      const as = String(a.symbol || "");
      const bs = String(b.symbol || "");
      return as.localeCompare(bs);
    });

    if (sortDir === "desc") sorted.reverse();
    return sorted;
  }, [tokens, searchTerm, sortBy, sortDir]);

  const visibleTokens = useMemo(() => {
    if (!onlyAnomalies) return filteredSorted;
    return filteredSorted.filter((t) => t.is_anomaly === true);
  }, [filteredSorted, onlyAnomalies]);

  const fetchHistory = async (symbol, interval) => {
    try {
      setHistoryLoading(true);
      setHistoryErr("");
      const res = await axios.get(
        `${API_BASE}/api/history/${encodeURIComponent(symbol)}?interval=${encodeURIComponent(interval)}`
      );

      const rows = Array.isArray(res.data) ? res.data : [];

      const data = rows
        .map((r) => {
          const ts = Number(r.time ?? r.openTime ?? r.t ?? r[0]);
          const o = Number(r.open ?? r.o ?? r[1]);
          const h = Number(r.high ?? r.h ?? r[2]);
          const l = Number(r.low ?? r.l ?? r[3]);
          const c = Number(r.close ?? r.c ?? r[4]);

          if (
            !Number.isFinite(ts) ||
            !Number.isFinite(o) ||
            !Number.isFinite(h) ||
            !Number.isFinite(l) ||
            !Number.isFinite(c)
          ) {
            return null;
          }

          return { x: new Date(ts), y: [o, h, l, c] };
        })
        .filter(Boolean);

      setCandleSeries([{ data }]);
    } catch (e) {
      setHistoryErr(e?.message || "History API error");
      setCandleSeries([{ data: [] }]);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (!selected?.symbol) return;
    fetchHistory(selected.symbol, timeframe);
  }, [selected, timeframe]);

  const chartOptions = useMemo(
    () => ({
      chart: { type: "candlestick", height: 350, toolbar: { show: true } },
      xaxis: { type: "datetime" },
      yaxis: { tooltip: { enabled: true } },
    }),
    []
  );

  const openReport = async () => {
    setReportOpen(true);
    if (report) return;

    try {
      setReportLoading(true);
      setReportErr("");
      const res = await axios.get(`${API_BASE}/api/analysis`);
      setReport(res.data && typeof res.data === "object" ? res.data : null);
    } catch (e) {
      setReportErr(e?.message || "Report API error");
      setReport(null);
    } finally {
      setReportLoading(false);
    }
  };

  const refreshReport = async () => {
    try {
      setReportLoading(true);
      setReportErr("");
      const res = await axios.get(`${API_BASE}/api/analysis`);
      setReport(res.data && typeof res.data === "object" ? res.data : null);
    } catch (e) {
      setReportErr(e?.message || "Report API error");
      setReport(null);
    } finally {
      setReportLoading(false);
    }
  };

  const corrKeys = useMemo(() => {
    const cm = report?.corr_matrix;
    if (!cm || typeof cm !== "object") return [];
    return Object.keys(cm);
  }, [report]);

  const topMetrics = useMemo(() => {
    if (!report || typeof report !== "object") return [];
    const skip = new Set(["corr_matrix", "heatmap_image"]);
    return Object.entries(report)
      .filter(([k, v]) => !skip.has(k))
      .filter(([_, v]) => typeof v === "string" || typeof v === "number" || typeof v === "boolean")
      .slice(0, 8);
  }, [report]);

  const formatMetricLabel = (k) =>
    String(k)
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());

  const formatVal = (v) => {
    if (typeof v === "number") {
      const abs = Math.abs(v);
      if (abs >= 1000) return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
      return v.toLocaleString(undefined, { maximumFractionDigits: 6 });
    }
    return String(v);
  };

  return (
    <div style={{ padding: 20, fontFamily: "Arial" }}>
      <h2>Crypto Analytics</h2>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginBottom: 12 }}>
        <label>
          Source:&nbsp;
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="live">Live (Binance API)</option>
            <option value="scraped">Scraped (Web)</option>
          </select>
        </label>

        <label>
          Search:&nbsp;
          <input value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="BTC, ETH..." />
        </label>

        <label>
          Sort:&nbsp;
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="symbol">Symbol</option>
            <option value="price">Price</option>
          </select>
        </label>

        <label>
          Direction:&nbsp;
          <select value={sortDir} onChange={(e) => setSortDir(e.target.value)}>
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
          </select>
        </label>

        <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} />
          Auto refresh (30s)
        </label>

        <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <input type="checkbox" checked={onlyAnomalies} onChange={(e) => setOnlyAnomalies(e.target.checked)} />
          Show anomalies only
        </label>

        <button onClick={fetchData} disabled={loading}>
          {loading ? "Loading..." : "Refresh"}
        </button>

        <button onClick={exportJSON} disabled={!tokens?.length}>
          Export JSON
        </button>

        <button onClick={exportCSV} disabled={!tokens?.length}>
          Export CSV
        </button>

        <button onClick={openReport}>Open Intelligence Report</button>

        <span style={{ opacity: 0.7 }}>
          Showing: {visibleTokens.length} / {tokens.length}
        </span>
      </div>

      {err && <p style={{ color: "red" }}>Error: {err}</p>}
      {loading && <p>Loading...</p>}

      {!loading && !err && (
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 10 }}>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 8 }}>Endpoint: {endpoint}</div>

          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {visibleTokens.map((t, i) => (
              <li key={t.symbol || i} style={{ marginBottom: 10 }}>
                <button
                  onClick={() => setSelected(t)}
                  style={{
                    border: "none",
                    background: "transparent",
                    padding: 0,
                    cursor: "pointer",
                    textDecoration: "underline",
                  }}
                >
                  <b>{t.symbol}</b>
                </button>{" "}
                <span style={{ opacity: 0.85 }}>
                  — {t.current_price ?? t.price ?? t.lastPrice ?? t.close ?? "-"} (
                  {(t.price_change_percentage_24h ?? 0).toFixed(3)}% / 24h)
                </span>{" "}
                {t.is_anomaly ? (
                  <span
                    style={{
                      marginLeft: 8,
                      padding: "2px 8px",
                      borderRadius: 999,
                      fontSize: 12,
                      fontWeight: 800,
                      background: "#ffe5e5",
                      color: "#b00020",
                      border: "1px solid #ffb3b3",
                    }}
                  >
                    ANOMALY • {(t.anomaly_score ?? 0).toFixed(3)}
                  </span>
                ) : (
                  <span
                    style={{
                      marginLeft: 8,
                      padding: "2px 8px",
                      borderRadius: 999,
                      fontSize: 12,
                      fontWeight: 800,
                      background: "#e8fff1",
                      color: "#0a7a2f",
                      border: "1px solid #b7f3ce",
                    }}
                  >
                    OK • {(t.anomaly_score ?? 0).toFixed(3)}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {selected && (
        <div
          onClick={() => setSelected(null)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 20,
            zIndex: 50,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ width: "min(900px, 95vw)", background: "#fff", borderRadius: 12, padding: 16 }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
              <h3 style={{ margin: 0 }}>{selected.symbol} History</h3>
              <button onClick={() => setSelected(null)}>Close</button>
            </div>

            <div style={{ marginTop: 10, display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
              <div style={{ padding: "6px 10px", borderRadius: 10, border: "1px solid #e5e5e5", background: "#fafafa" }}>
                <div style={{ fontSize: 12, opacity: 0.7 }}>Current Price</div>
                <div style={{ fontSize: 18, fontWeight: 800 }}>
                  {selected.current_price ?? selected.price ?? "-"}
                </div>
              </div>

              <div style={{ padding: "6px 10px", borderRadius: 10, border: "1px solid #e5e5e5", background: "#fafafa" }}>
                <div style={{ fontSize: 12, opacity: 0.7 }}>24h Change</div>
                <div style={{ fontSize: 18, fontWeight: 800 }}>
                  {(selected.price_change_percentage_24h ?? 0).toFixed(3)}%
                </div>
              </div>

              <div style={{ padding: "6px 10px", borderRadius: 10, border: "1px solid #e5e5e5", background: "#fafafa" }}>
                <div style={{ fontSize: 12, opacity: 0.7 }}>Anomaly</div>
                <div style={{ fontSize: 18, fontWeight: 900, color: selected.is_anomaly ? "#b00020" : "#0a7a2f" }}>
                  {selected.is_anomaly ? "TRUE" : "FALSE"} • {(selected.anomaly_score ?? 0).toFixed(3)}
                </div>
              </div>

              <div style={{ padding: "6px 10px", borderRadius: 10, border: "1px solid #e5e5e5", background: "#fafafa" }}>
                <div style={{ fontSize: 12, opacity: 0.7 }}>Market Rank</div>
                <div style={{ fontSize: 18, fontWeight: 800 }}>
                  {selected.market_cap_rank ?? "-"}
                </div>
              </div>
            </div>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginTop: 12 }}>
              <label>
                Timeframe:&nbsp;
                <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
                  <option value="15m">15m</option>
                  <option value="1h">1h</option>
                  <option value="4h">4h</option>
                  <option value="1d">1d</option>
                  <option value="1w">1w</option>
                  <option value="1M">1M</option>
                </select>
              </label>

              <span style={{ opacity: 0.7 }}>
                {historyLoading
                  ? "Loading history..."
                  : candleSeries?.[0]?.data?.length
                  ? `Candles: ${candleSeries[0].data.length}`
                  : "No data"}
              </span>
            </div>

            {historyErr && <p style={{ color: "red" }}>Error: {historyErr}</p>}

            <div style={{ marginTop: 10 }}>
              <Chart options={chartOptions} series={candleSeries} type="candlestick" height={380} />
            </div>
          </div>
        </div>
      )}

      {reportOpen && (
        <div
          onClick={() => setReportOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.55)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 20,
            zIndex: 60,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: "min(1100px, 96vw)",
              maxHeight: "90vh",
              overflow: "auto",
              background: "#fff",
              borderRadius: 12,
              padding: 16,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
              <h3 style={{ margin: 0 }}>Algorithmic Market Intelligence Report</h3>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <button onClick={refreshReport} disabled={reportLoading}>
                  {reportLoading ? "Refreshing..." : "Refresh"}
                </button>
                <button onClick={exportReportJSON} disabled={!report}>
                  Export Report JSON
                </button>
                <button onClick={() => setReportOpen(false)}>Close</button>
              </div>
            </div>

            <div style={{ marginTop: 10, fontSize: 12, opacity: 0.7 }}>
              Endpoint: /api/analysis
            </div>

            {reportErr && <p style={{ color: "red" }}>Error: {reportErr}</p>}
            {reportLoading && <p>Loading report...</p>}

            {!reportLoading && report && (
              <div style={{ marginTop: 12 }}>
                {topMetrics.length > 0 && (
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                      gap: 10,
                      marginBottom: 14,
                    }}
                  >
                    {topMetrics.map(([k, v]) => (
                      <div
                        key={k}
                        style={{
                          border: "1px solid #e5e5e5",
                          borderRadius: 10,
                          padding: 10,
                          background: "#fafafa",
                        }}
                      >
                        <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 6 }}>
                          {formatMetricLabel(k)}
                        </div>
                        <div style={{ fontSize: 18, fontWeight: 700 }}>
                          {formatVal(v)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {report.heatmap_image && (
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontWeight: 700, marginBottom: 8 }}>Correlation Heatmap</div>
                    <img
                      src={report.heatmap_image}
                      alt="Correlation Heatmap"
                      style={{ width: "100%", maxWidth: 900, border: "1px solid #e5e5e5", borderRadius: 10 }}
                    />
                  </div>
                )}

                {corrKeys.length > 0 && (
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontWeight: 700, marginBottom: 8 }}>Correlation Matrix</div>
                    <div style={{ overflowX: "auto" }}>
                      <table style={{ borderCollapse: "collapse", width: "100%", minWidth: 600 }}>
                        <thead>
                          <tr>
                            <th style={{ border: "1px solid #e5e5e5", padding: 8, background: "#fafafa", textAlign: "left" }}>
                              Metric
                            </th>
                            {corrKeys.map((k) => (
                              <th key={k} style={{ border: "1px solid #e5e5e5", padding: 8, background: "#fafafa", textAlign: "left" }}>
                                {k}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {corrKeys.map((rowKey) => (
                            <tr key={rowKey}>
                              <td style={{ border: "1px solid #e5e5e5", padding: 8, fontWeight: 700 }}>
                                {rowKey}
                              </td>
                              {corrKeys.map((colKey) => {
                                const val = report?.corr_matrix?.[rowKey]?.[colKey];
                                const num = typeof val === "number" ? val : Number(val);
                                const display = Number.isFinite(num) ? num.toFixed(6) : "-";
                                return (
                                  <td key={colKey} style={{ border: "1px solid #e5e5e5", padding: 8 }}>
                                    {display}
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <input type="checkbox" checked={showRawReport} onChange={(e) => setShowRawReport(e.target.checked)} />
                    Show raw JSON
                  </label>
                </div>

                {showRawReport && (
                  <pre
                    style={{
                      marginTop: 10,
                      padding: 12,
                      background: "#111",
                      color: "#eee",
                      borderRadius: 10,
                      overflow: "auto",
                      maxHeight: 320,
                      fontSize: 12,
                    }}
                  >
                    {JSON.stringify(report, null, 2)}
                  </pre>
                )}
              </div>
            )}

            {!reportLoading && !report && !reportErr && <p>No report data.</p>}
          </div>
        </div>
      )}
    </div>
  );
}
