import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import Chart from "react-apexcharts";
import "./App.css";

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
    return () => { cancelled = true; };
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
      
      const data = rows.map((r) => {
          if (r.x && r.y) {
              return { x: new Date(r.x), y: r.y };
          }
          
          const ts = Number(r.time ?? r.openTime ?? r.t ?? r[0]);
          const o = Number(r.open ?? r.o ?? r[1]);
          const h = Number(r.high ?? r.h ?? r[2]);
          const l = Number(r.low ?? r.l ?? r[3]);
          const c = Number(r.close ?? r.c ?? r[4]);
          
          if (!Number.isFinite(ts) || !Number.isFinite(o)) return null;
          return { x: new Date(ts), y: [o, h, l, c] };
        }).filter(Boolean);

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

  const chartOptions = useMemo(() => ({
    chart: { type: "candlestick", height: 350, toolbar: { show: true }, background: 'transparent' },
    theme: { mode: 'dark' },
    xaxis: { type: "datetime" },
    yaxis: { tooltip: { enabled: true } },
    grid: { borderColor: '#333' }
  }), []);

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

  const topMetrics = useMemo(() => {
    if (!report || typeof report !== "object") return [];
    const skip = new Set(["corr_matrix", "heatmap_image"]);
    return Object.entries(report)
      .filter(([k, v]) => !skip.has(k))
      .filter(([_, v]) => typeof v === "string" || typeof v === "number" || typeof v === "boolean")
      .slice(0, 8);
  }, [report]);

  const formatMetricLabel = (k) => String(k).replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  const formatVal = (v) => {
    if (typeof v === "number") {
      const abs = Math.abs(v);
      if (abs >= 1000) return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
      return v.toLocaleString(undefined, { maximumFractionDigits: 6 });
    }
    return String(v);
  };

  return (
    <div className="nexus-container">
      <header className="nexus-header">
        <h2>NEXUS_TERMINAL_PRO_V1</h2>
        <div className="status-badge">SYSTEM: ONLINE</div>
      </header>

      <div className="control-panel">
        <div className="control-group">
          <select className="nexus-select" value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="live">⚡ Live Feed (Binance)</option>
            <option value="scraped">🕷 Scraped Data</option>
          </select>

          <input 
            className="nexus-input" 
            value={searchTerm} 
            onChange={(e) => setSearchTerm(e.target.value)} 
            placeholder="SEARCH ASSET (e.g. BTC)..." 
          />
        </div>

        <div className="control-group">
          <select className="nexus-select" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="symbol">Sort: Symbol</option>
            <option value="price">Sort: Price</option>
          </select>

          <select className="nexus-select" value={sortDir} onChange={(e) => setSortDir(e.target.value)}>
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
          </select>
        </div>

        <div className="control-group checkboxes">
          <label className="nexus-checkbox">
            <input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} />
            <span>AUTO-SYNC (30s)</span>
          </label>

          <label className="nexus-checkbox">
            <input type="checkbox" checked={onlyAnomalies} onChange={(e) => setOnlyAnomalies(e.target.checked)} />
            <span>ANOMALIES ONLY</span>
          </label>
        </div>

        <div className="action-buttons">
          <button className="nexus-btn primary" onClick={fetchData} disabled={loading}>
            {loading ? "SYNCING..." : "REFRESH DATA"}
          </button>
          <button className="nexus-btn" onClick={exportJSON} disabled={!tokens?.length}>JSON</button>
          <button className="nexus-btn" onClick={exportCSV} disabled={!tokens?.length}>CSV</button>
          <button className="nexus-btn highlight" onClick={openReport}>INTELLIGENCE REPORT</button>
        </div>
      </div>

      <div className="data-display-area">
        <div className="meta-info">
          <span>ENDPOINT: {endpoint}</span>
          <span>VISIBLE: {visibleTokens.length} / {tokens.length}</span>
        </div>
        
        {err && <div className="nexus-alert error">CRITICAL ERROR: {err}</div>}
        {loading && <div className="nexus-loader">ESTABLISHING CONNECTION...</div>}

        {!loading && !err && (
          <div className="token-grid">
            {visibleTokens.map((t, i) => (
              <div key={t.symbol || i} className={`token-card ${t.is_anomaly ? 'anomaly-detected' : ''}`} onClick={() => setSelected(t)}>
                <div className="card-header">
                  <span className="symbol">{t.symbol}</span>
                  <span className={`rank-badge`}>#{t.market_cap_rank}</span>
                </div>
                
                <div className="price-display">
                  {t.current_price ?? t.price ?? "-"}
                </div>
                
                <div className={`change-display ${(t.price_change_percentage_24h ?? 0) >= 0 ? 'pos' : 'neg'}`}>
                  {(t.price_change_percentage_24h ?? 0).toFixed(2)}%
                </div>

                <div className="status-footer">
                  {t.is_anomaly ? (
                    <span className="status-tag anomaly">⚠️ ANOMALY ({t.anomaly_score?.toFixed(2)})</span>
                  ) : (
                    <span className="status-tag ok">✔ STABLE</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selected && (
        <div className="nexus-modal-overlay" onClick={() => setSelected(null)}>
          <div className="nexus-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selected.symbol} // MARKET DATA</h3>
              <button className="close-btn" onClick={() => setSelected(null)}>X</button>
            </div>

            <div className="modal-stats-grid">
              <div className="stat-box">
                <label>CURRENT PRICE</label>
                <div className="val">{selected.current_price ?? selected.price ?? "-"}</div>
              </div>
              <div className="stat-box">
                <label>24H CHANGE</label>
                <div className={`val ${(selected.price_change_percentage_24h ?? 0) >= 0 ? 'pos' : 'neg'}`}>
                  {(selected.price_change_percentage_24h ?? 0).toFixed(3)}%
                </div>
              </div>
              <div className={`stat-box ${selected.is_anomaly ? 'anomaly-box' : ''}`}>
                <label>STATUS</label>
                <div className="val">{selected.is_anomaly ? "ANOMALY DETECTED" : "NORMAL"}</div>
              </div>
            </div>

            <div className="chart-controls">
              <select className="nexus-select small" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
                {['15m','1h','4h','1d','1w','1M'].map(tf => <option key={tf} value={tf}>{tf}</option>)}
              </select>
              <span>{historyLoading ? "LOADING CANDLES..." : ""}</span>
            </div>

            {historyErr ? (
              <p className="error-text">{historyErr}</p>
            ) : (
              <div className="chart-container">
                <Chart options={chartOptions} series={candleSeries} type="candlestick" height={350} />
              </div>
            )}
          </div>
        </div>
      )}

      {reportOpen && (
        <div className="nexus-modal-overlay" onClick={() => setReportOpen(false)}>
          <div className="nexus-modal large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>ALGORITHMIC MARKET INTELLIGENCE</h3>
              <div className="header-actions">
                <button className="nexus-btn small" onClick={refreshReport}>REFRESH</button>
                <button className="nexus-btn small" onClick={() => setReportOpen(false)}>CLOSE</button>
              </div>
            </div>

            {reportLoading && <div className="nexus-loader">ANALYZING MARKET DATA...</div>}
            
            {!reportLoading && report && (
              <div className="report-content">
                <div className="metrics-grid">
                  {topMetrics.map(([k, v]) => (
                    <div key={k} className="metric-card">
                      <label>{formatMetricLabel(k)}</label>
                      <div className="metric-val">{formatVal(v)}</div>
                    </div>
                  ))}
                </div>

                <div className="visuals-grid">
                  {report.heatmap_image && (
                    <div className="visual-card">
                      <h4>CORRELATION HEATMAP</h4>
                      <img src={report.heatmap_image} alt="Heatmap" />
                    </div>
                  )}
                </div>

                <div className="raw-data-section">
                   <button className="nexus-btn small" onClick={() => setShowRawReport(!showRawReport)}>
                     {showRawReport ? "HIDE RAW DATA" : "SHOW RAW JSON"}
                   </button>
                   {showRawReport && (
                     <pre className="raw-json">{JSON.stringify(report, null, 2)}</pre>
                   )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}