import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Chart from 'react-apexcharts'; // Mum Grafiği
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';

function App() {
  const [tokens, setTokens] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [source, setSource] = useState('API'); 
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Modal ve Grafik State'leri
  const [selectedCoin, setSelectedCoin] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [timeframe, setTimeframe] = useState('1h');

  // --- VERİ ÇEKME ---
  const fetchData = async () => {
    try {
      const endpoint = source === 'API' 
        ? 'http://127.0.0.1:5000/api/live-data' 
        : 'http://127.0.0.1:5000/api/scraped-data';
      
      const res = await axios.get(endpoint);
      
      if (res.data && Array.isArray(res.data) && res.data.length > 0) {

        // ✅ KRİTİK: Rank 1→50 bozulmasın diye market_cap_rank'a göre sıralıyoruz
        const stableData = res.data.sort((a, b) => {
          const ra = Number(a.market_cap_rank) || 999999;
          const rb = Number(b.market_cap_rank) || 999999;
          if (ra !== rb) return ra - rb;
          return (a.symbol || "").localeCompare(b.symbol || "");
        });

        setTokens(stableData);
      }
    } catch (err) { 
      console.error("Veri Hatası:", err); 
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalysis = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:5000/api/analysis');
      setAnalysis(res.data);
    } catch (err) { console.error("Analiz Hatası:", err); }
  };

  // --- GRAFİK VERİSİ ---
  const fetchCoinHistory = async (coinSymbol, interval) => {
    setHistoryLoading(true);
    setHistoryData([]); 
    try {
      const res = await axios.get(`http://127.0.0.1:5000/api/history/${coinSymbol}?interval=${interval}`);
      if (res.data) {
        setHistoryData(res.data);
      }
    } catch (err) { 
        console.error("Geçmiş Veri Hatası:", err); 
    } finally {
        setHistoryLoading(false);
    }
  };

  const openCoinDetails = (coin) => {
    setSelectedCoin(coin);
    setTimeframe('1h'); 
    fetchCoinHistory(coin.symbol, '1h');
  };

  const changeTimeframe = (newTimeframe) => {
    setTimeframe(newTimeframe);
    if (selectedCoin) {
      fetchCoinHistory(selectedCoin.symbol, newTimeframe);
    }
  };

  useEffect(() => {
    setLoading(true); 
    setTokens([]); 
    fetchData();

    // ✅ İSTEĞİN: API hızını 0.2 saniyeden çekmiyoruz
    const intervalTime = source === 'API' ? 200 : 15000;

    const interval = setInterval(fetchData, intervalTime); 
    return () => clearInterval(interval);
  }, [source]);

  const filteredTokens = tokens.filter(token => {
    if (!searchTerm) return true;
    const lowerTerm = searchTerm.toLowerCase();
    return token.symbol.toLowerCase().includes(lowerTerm) || token.name.toLowerCase().includes(lowerTerm);
  });

  // Candlestick Chart Ayarları
  const candlestickOptions = {
    chart: { type: 'candlestick', height: 350, toolbar: { show: false }, background: 'transparent' },
    title: { text: selectedCoin ? `${selectedCoin.name} (${timeframe.toUpperCase()})` : '', style: { color: '#fff' } },
    xaxis: { type: 'datetime', labels: { style: { colors: '#888' } } },
    yaxis: { tooltip: { enabled: true }, labels: { style: { colors: '#888' }, formatter: (val) => `$${val.toFixed(2)}` } },
    grid: { borderColor: '#333' },
    theme: { mode: 'dark' },
    plotOptions: { candlestick: { colors: { upward: '#00d1b2', downward: '#ff3860' } } }
  };

  // --- CSS ---
  const styles = `
    body { margin: 0; font-family: 'Inter', sans-serif; background-color: #050505; }
    ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: #000; } ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
    .glass-card { background: rgba(20, 20, 20, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 24px; }
    .glass-card:hover { border-color: rgba(0, 209, 178, 0.3); transition: 0.3s; }
    .modern-btn { border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; color: white; text-transform: uppercase; letter-spacing: 1px; }
    .btn-hover:hover { filter: brightness(1.2); transform: translateY(-2px); transition: 0.2s; }
    .table-row { border-bottom: 1px solid rgba(255,255,255,0.03); cursor: pointer; }
    .table-row:hover { background: rgba(0, 209, 178, 0.1) !important; transition: 0.2s; }
    .table-row td { white-space: nowrap; transition: none; } 
    .numeric-cell { font-variant-numeric: tabular-nums; }
    
    .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 99999; display: flex; justify-content: center; align-items: center; }
    .modal-content { background: #151515; width: 90%; max-width: 900px; padding: 30px; border-radius: 20px; border: 1px solid #333; position: relative; box-shadow: 0 0 50px rgba(0,209,178,0.2); }
    .close-btn { position: absolute; top: 15px; right: 20px; font-size: 28px; color: #666; cursor: pointer; }
    .close-btn:hover { color: #fff; }
    .time-btn { background: #222; border: 1px solid #333; color: #888; padding: 5px 15px; margin-right: 10px; border-radius: 5px; cursor: pointer; font-weight: bold; transition: 0.2s; }
    .time-btn:hover { background: #333; color: #fff; }
    .time-btn.active { background: #00d1b2; color: #000; border-color: #00d1b2; }
  `;

  // --- YÜKLEME EKRANI ---
  if (loading && tokens.length === 0) {
    return (
      <div style={{height:'100vh', background:'#050505', color:'white', display:'flex', flexDirection:'column', justifyContent:'center', alignItems:'center'}}>
        <div style={{width:'50px', height:'50px', border:'3px solid #333', borderTop:'3px solid #00d1b2', borderRadius:'50%', animation:'spin 1s infinite'}}></div>
        <p style={{marginTop:'20px'}}>Booting Nexus Terminal...</p>
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#050505', color: '#ccc', padding: '40px 20px', backgroundImage: 'radial-gradient(circle at top center, #111 0%, #050505 60%)' }}>
      <style>{styles}</style>

      {/* ✅ POP-UP MODAL (satıra tıklayınca grafik açılır) */}
      {selectedCoin && (
        <div className="modal-overlay" onClick={() => setSelectedCoin(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <span className="close-btn" onClick={() => setSelectedCoin(null)}>&times;</span>
            
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'20px', flexWrap:'wrap', gap:'10px'}}>
              <div style={{display:'flex', alignItems:'center', gap:'15px'}}>
                <h2 style={{margin:0, color:'#fff'}}>{selectedCoin.name} <span style={{color:'#666'}}>({selectedCoin.symbol})</span></h2>
                <span style={{color: (Number(selectedCoin.price_change_percentage_24h) || 0) > 0 ? '#00d1b2':'#ff3860', fontSize:'1.2rem', fontWeight:'bold'}}>
                  ${selectedCoin.current_price?.toLocaleString()}
                </span>
              </div>
              <div>
                {['15m', '1h', '4h', '1d', '1w', '1M'].map((t) => (
                  <button key={t} className={`time-btn ${timeframe===t?'active':''}`} onClick={() => changeTimeframe(t)}>{t.toUpperCase()}</button>
                ))}
              </div>
            </div>

            {historyLoading ? (
              <div style={{textAlign:'center', padding:'60px', color:'#666'}}>Syncing Market Data...</div>
            ) : (
              historyData.length > 0 ? (
                <Chart options={candlestickOptions} series={[{data: historyData}]} type="candlestick" height={400} />
              ) : (
                <div style={{textAlign:'center', padding:'60px', color:'#ff3860'}}>Data Source Unavailable</div>
              )
            )}
          </div>
        </div>
      )}

      {/* HEADER */}
      <div style={{ textAlign: 'center', marginBottom: '50px' }}>
        <h1 style={{ fontSize: '3rem', margin: '0', background: 'linear-gradient(to right, #fff, #888)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontFamily: 'monospace', letterSpacing: '-2px' }}>
          NEXUS_TERMINAL_PRO_V1
        </h1>
        <div style={{fontSize:'0.8rem', color:'#555', marginTop:'10px'}}>INSTITUTIONAL MARKET DATA • NEURAL NET PREDICTION • ALGORITHMIC TRADING</div>
      </div>

      {/* CONTROLS */}
      <div style={{ maxWidth: '1400px', margin: '0 auto 40px auto', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '20px' }}>
        <div style={{ display: 'flex', gap: '15px' }}>
          <button className="modern-btn btn-hover" onClick={() => setSource('API')} style={{ background: source==='API' ? '#00d1b2':'#1a1a1a', color: source==='API'?'#000':'#fff' }}>⚡ Live Exchange Feed</button>
          <button className="modern-btn btn-hover" onClick={() => setSource('SCRAPER')} style={{ background: source==='SCRAPER' ? '#f29f05':'#1a1a1a', color: source==='SCRAPER'?'#000':'#fff' }}>🕷 Web Mining Node</button>
          <button className="modern-btn btn-hover" onClick={fetchAnalysis} style={{ background: '#7957d5', color: '#fff' }}>📊 Deploy Intelligence Report</button>
        </div>
        <input type="text" placeholder="🔍 Search Asset (e.g. BTC)..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} style={{padding:'12px 20px', borderRadius:'8px', border:'1px solid #333', background:'#111', color:'#fff', outline:'none', minWidth:'300px'}} />
      </div>

      {/* GRID (Grafik + Analiz geri geldi) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '25px', maxWidth: '1400px', margin: '0 auto' }}>
        {/* BAR CHART */}
        <div className="glass-card" style={{ minHeight: '400px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ marginBottom: '20px' }}><h3 style={{ margin: 0, color: '#fff' }}>VOLATILITY INDEX & PRICE ACTION</h3></div>
          <div style={{ flex: 1 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={filteredTokens.slice(0, 10)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                <XAxis dataKey="symbol" stroke="#444" tick={{fontSize: 10}} axisLine={false} tickLine={false} />
                <YAxis stroke="#444" domain={['auto', 'auto']} width={50} axisLine={false} tickLine={false} tick={{fontSize: 10}} /> 
                <Tooltip cursor={{fill: 'rgba(255,255,255,0.02)'}} contentStyle={{ backgroundColor: '#000', border: '1px solid #333' }} itemStyle={{ color: '#fff' }} />
                <Bar dataKey="current_price" radius={[4, 4, 0, 0]} isAnimationActive={true}>
                  {filteredTokens.slice(0, 10).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.is_anomaly ? '#ff3860' : '#00d1b2'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* ANALYSIS REPORT */}
        {analysis && analysis.stats && (
          <div className="glass-card" style={{ borderLeft: '4px solid #7957d5' }}>
            <h3 style={{ margin: '0 0 20px 0', color: '#a084fa' }}>ALGORITHMIC MARKET INTELLIGENCE</h3>

            <div style={{ display: 'flex', gap: '20px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '20px' }}>
              <div style={{ flex: 1 }}>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.85rem', lineHeight: '1.8' }}>
                  <li style={{ borderBottom: '1px solid #222', display: 'flex', justifyContent: 'space-between' }}><span>Mean Price</span> <span style={{color: '#fff'}}>${analysis.stats?.mean}</span></li>
                  <li style={{ borderBottom: '1px solid #222', display: 'flex', justifyContent: 'space-between' }}><span>Skewness</span> <span style={{color: '#00d1b2'}}>{analysis.stats?.skewness}</span></li>
                  <li style={{ borderBottom: '1px solid #222', display: 'flex', justifyContent: 'space-between' }}><span>Kurtosis</span> <span style={{color: '#00d1b2'}}>{analysis.stats?.kurtosis}</span></li>
                </ul>
                <div style={{ marginTop: '10px', color: '#ff3860', fontSize: '0.8rem', fontWeight: 'bold' }}>⚠ {analysis.stats?.outliers_count} MARKET ANOMALIES DETECTED</div>
              </div>

              {analysis.prediction && (
                <div style={{ background:'rgba(255,255,255,0.05)', padding:'10px', borderRadius:'10px', minWidth:'140px', textAlign:'center', border:'1px solid rgba(121, 87, 213, 0.3)' }}>
                  <div style={{fontSize:'0.7rem', color:'#a084fa', marginBottom:'5px'}}>NEURAL NET FORECAST ({analysis.prediction.target_coin})</div>
                  <div style={{fontSize:'1.1rem', fontWeight:'bold', color: analysis.prediction.trend === 'UP' ? '#00d1b2' : '#ff3860'}}>
                    {analysis.prediction.trend === 'UP' ? '▲' : '▼'} ${analysis.prediction.predicted_next}
                  </div>
                  <div style={{fontSize:'0.6rem', color:'#666'}}>Regression Model v2.1</div>
                </div>
              )}

              {analysis.sentiment && (
                <div style={{ background:'rgba(255,255,255,0.05)', padding:'10px', borderRadius:'10px', minWidth:'140px', textAlign:'center', border:'1px solid rgba(0, 209, 178, 0.3)' }}>
                  <div style={{fontSize:'0.7rem', color:'#00d1b2', marginBottom:'5px'}}>GLOBAL SENTIMENT INDEX</div>
                  <div style={{fontSize:'0.9rem', fontWeight:'bold', color:'#fff'}}>{analysis.sentiment.market_status}</div>
                  <div style={{fontSize:'0.6rem', color:'#666'}}>Score: {analysis.sentiment.sentiment_score}</div>
                </div>
              )}
            </div>

            <div style={{display:'flex', gap:'10px'}}>
              <div style={{ flex: 1, textAlign: 'center', minWidth: '150px' }}>
                 <p style={{fontSize:'0.7rem', color:'#666'}}>Distribution (Box Plot)</p>
                 {analysis.plot_image && <img src={analysis.plot_image} alt="Box Plot" style={{ width: '100%', borderRadius: '8px', border: '1px solid #333' }} />}
              </div>
              <div style={{ flex: 1, textAlign: 'center', minWidth: '150px' }}>
                 <p style={{fontSize:'0.7rem', color:'#666'}}>Correlation (Heatmap)</p>
                 {analysis.heatmap_image && <img src={analysis.heatmap_image} alt="Heatmap" style={{ width: '100%', borderRadius: '8px', border: '1px solid #333' }} />}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* TABLE (satıra tıklayınca modal açılır) */}
      <div className="glass-card" style={{ maxWidth: '1400px', margin: '30px auto 0 auto', padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}><h3 style={{ margin: 0, color: '#fff' }}>ACTIVE MARKET PAIRS</h3></div>
        <div style={{ overflowX: 'auto', maxHeight: '600px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
              <thead style={{ position: 'sticky', top: 0, background: '#0a0a0a', zIndex: 10 }}>
                <tr style={{ textAlign: 'left', color: '#444', textTransform: 'uppercase', fontSize: '0.75rem' }}>
                  <th style={{ padding: '15px 25px' }}>Rank</th>
                  <th style={{ padding: '15px 25px' }}>Token</th>
                  <th style={{ padding: '15px 25px' }}>Price</th>
                  <th style={{ padding: '15px 25px' }}>24h Change</th>
                  <th style={{ padding: '15px 25px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredTokens.map((t) => {
                  const change24h = Number(t.price_change_percentage_24h) || 0;
                  return (
                    <tr key={t.symbol} className="table-row" onClick={() => openCoinDetails(t)}>
                      <td style={{ padding: '15px 25px', color: '#555' }}>{t.market_cap_rank}</td>
                      <td style={{ padding: '15px 25px' }}><span style={{fontWeight:'700', color:'#fff'}}>{t.symbol}</span> <span style={{fontSize:'0.8em', color:'#666'}}>{t.name}</span></td>
                      <td style={{ padding: '15px 25px', fontFamily:'monospace', color:'#ccc' }} className="numeric-cell">${t.current_price?.toLocaleString()}</td>
                      <td style={{ padding: '15px 25px' }}>
                        <span style={{
                            color: change24h > 0 ? '#00d1b2' : '#ff3860',
                            display: 'inline-block',
                            minWidth: '60px',
                            fontVariantNumeric: 'tabular-nums'
                        }}>
                          {change24h > 0 ? '+' : ''}{change24h.toFixed(2)}%
                        </span>
                      </td>
                      <td style={{ padding: '15px 25px' }}>{t.is_anomaly ? <span style={{color:'#ff3860', fontSize:'0.7rem', border:'1px solid #ff3860', padding:'2px 8px', borderRadius:'10px'}}>ANOMALY</span> : <span style={{color:'#444', fontSize:'0.7rem'}}>OK</span>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
        </div>
      </div>
    </div>
  );
}

export default App;
