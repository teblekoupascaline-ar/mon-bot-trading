import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="Terminal Trading", layout="wide", initial_sidebar_state="expanded")

# --- CSS SUR MESURE (TRADINGVIEW STYLE) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp {
        background-color: #131722; 
        font-family: 'Inter', sans-serif;
        color: #d1d4dc !important;
    }

    div, p, span, label {
        color: #d1d4dc !important;
    }

    .top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #1e222d;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
        border: 1px solid #2a2e39;
    }
    
    .metric-box { text-align: center; flex: 1; }
    .metric-label { font-size: 10px; color: #787b86 !important; text-transform: uppercase; }
    .metric-value { font-size: 16px; font-weight: 800; color: #ffffff !important; }

    .signal-buy { color: #089981 !important; }
    .signal-sell { color: #f23645 !important; }
    .signal-neutral { color: #fbc02d !important; }

    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(8, 153, 129, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(8, 153, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(8, 153, 129, 0); }
    }
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(242, 54, 69, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(242, 54, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(242, 54, 69, 0); }
    }
    
    .pulse-green { background: rgba(8, 153, 129, 0.15); border: 1px solid #089981; border-radius: 6px; padding: 5px 10px; animation: pulse-green 2s infinite; }
    .pulse-red { background: rgba(242, 54, 69, 0.15); border: 1px solid #f23645; border-radius: 6px; padding: 5px 10px; animation: pulse-red 2s infinite; }

    .action-box {
        background: #1e222d;
        border: 1px solid #2a2e39;
        border-radius: 8px;
        padding: 10px;
        margin-top: 10px;
    }
    
    .action-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        font-size: 14px;
        border-bottom: 1px solid #2a2e39;
        padding-bottom: 5px;
    }
    
    .badge-macro { background: rgba(30, 34, 45, 0.8); border: 1px solid #2a2e39; padding: 5px; border-radius: 4px; font-size: 12px; text-align: center; margin-bottom: 5px;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Paramètres Système")
    actifs = {
        "Bitcoin": "BTC-USD", 
        "Ethereum": "ETH-USD", 
        "Or (XAU/USD)": "GC=F", # <--- L'OR EST AJOUTÉ ICI
        "EUR/USD": "EURUSD=X", 
        "Apple": "AAPL", 
        "Tesla": "TSLA", 
        "S&P 500": "^GSPC"
    }
    choix_actif = st.selectbox("Actif", list(actifs.keys()))
    ticker = actifs[choix_actif]
    
    st.divider()
    capital = st.number_input("Capital ($)", min_value=10.0, value=50.0, step=10.0)
    risque_pct = st.slider("Risque (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
    
    if st.button("Actualiser", type="primary"):
        st.cache_data.clear()

@st.cache_data(ttl=60)
def charger_donnees(ticker):
    df = yf.download(ticker, period="2y", interval="1d", progress=False)
    df_w = yf.download(ticker, period="2y", interval="1wk", progress=False)
    for d in [df, df_w]:
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
    return df, df_w

# --- LOGIQUE PRINCIPALE ---
with st.spinner("Analyse..."):
    df, df_w = charger_donnees(ticker)
    
    if not df.empty and not df_w.empty:
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df = df.dropna()
        
        df_w['SMA_20'] = ta.sma(df_w['Close'], length=20)
        df_w = df_w.dropna()
        
        if df.empty or df_w.empty:
            st.error("Données insuffisantes.")
            st.stop()
            
        dernier = df.iloc[-1]
        avant = df.iloc[-2]
        dernier_w = df_w.iloc[-1]
        
        macro_bull = dernier_w['Close'] > dernier_w['SMA_20']
        micro_bull = dernier['SMA_20'] > dernier['SMA_50']
        
        score = 0
        raisons = []
        
        if macro_bull and micro_bull:
            score += 30
            raisons.append("Alignement parfait haussier (Macro + Micro).")
            align_txt = "Aligné Haussier"
            align_color = "#089981"
        elif not macro_bull and not micro_bull:
            score -= 30
            raisons.append("Alignement parfait baissier (Macro + Micro).")
            align_txt = "Aligné Baissier"
            align_color = "#f23645"
        else:
            raisons.append("Conflit de tendances (Macro et Micro ne sont pas d'accord).")
            align_txt = "Conflit de Tendance"
            align_color = "#fbc02d"
            
        if dernier['Close'] > dernier['SMA_200']:
            score += 20
            raisons.append("Prix au-dessus de la SMA 200 (Tendance de fond haussière).")
        else:
            score -= 20
            raisons.append("Prix en-dessous de la SMA 200 (Tendance de fond baissière).")
            
        if dernier['RSI'] < 30:
            score += 20
            raisons.append(f"RSI en survente ({dernier['RSI']:.1f}).")
        elif dernier['RSI'] > 70:
            score -= 20
            raisons.append(f"RSI en surachat ({dernier['RSI']:.1f}).")
        else:
            raisons.append(f"RSI neutre ({dernier['RSI']:.1f}).")

        prix = dernier['Close']
        variation = ((prix - avant['Close']) / avant['Close']) * 100
        
        if score >= 50: signal_txt, sig_class, pulse = "ACHAT FORT", "signal-buy", "pulse-green"
        elif score > 0: signal_txt, sig_class, pulse = "ACHAT", "signal-buy", ""
        elif score <= -50: signal_txt, sig_class, pulse = "VENTE FORTE", "signal-sell", "pulse-red"
        elif score < 0: signal_txt, sig_class, pulse = "VENTE", "signal-sell", ""
        else: signal_txt, sig_class, pulse = "NEUTRE", "signal-neutral", ""

        st.markdown(f"""
        <div class="top-bar">
            <div class="metric-box">
                <div class="metric-label">Prix</div>
                <div class="metric-value">{prix:,.2f}</div>
                <div style="font-size: 10px; color: {'#089981' if variation >= 0 else '#f23645'} !important;">{variation:+.2f}%</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">RSI</div>
                <div class="metric-value">{dernier['RSI']:.1f}</div>
            </div>
            <div class="metric-box {pulse}">
                <div class="metric-label">Signal</div>
                <div class="metric-value {sig_class}">{signal_txt}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_graph, col_info = st.columns([2, 1])

        with col_graph:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], 
                name="Prix", increasing_line_color='#089981', decreasing_line_color='#f23645'
            ))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#fbc02d', width=1), name="SMA 50"))
            
            if score >= 20 or score <= -20:
                is_long = score >= 20
                sl = prix - (dernier['ATR'] * 1.5) if is_long else prix + (dernier['ATR'] * 1.5)
                tp = prix + (dernier['ATR'] * 3.0) if is_long else prix - (dernier['ATR'] * 3.0)
                
                fig.add_hline(y=sl, line_dash="dash", line_color="#f23645", annotation_text="SL", annotation_position="top right")
                fig.add_hline(y=tp, line_dash="dash", line_color="#089981", annotation_text="TP", annotation_position="bottom right")

            x_min = df.index[-90] if len(df) > 90 else df.index[0]
            x_max = df.index[-1]

            fig.update_layout(
                height=500, 
                template="plotly_dark", 
                dragmode="pan", 
                paper_bgcolor='#131722', plot_bgcolor='#131722',
                margin=dict(l=5, r=5, t=30, b=5),
                xaxis=dict(
                    range=[x_min, x_max],
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1M", step="month", stepmode="backward"),
                            dict(count=3, label="3M", step="month", stepmode="backward"),
                            dict(count=6, label="6M", step="month", stepmode="backward"),
                            dict(count=1, label="1A", step="year", stepmode="backward"),
                            dict(step="all", label="Max")
                        ]),
                        bgcolor="#1e222d", activecolor="#2a2e39"
                    ),
                    rangeslider=dict(visible=True, bgcolor="#1e222d"), 
                    type="date", gridcolor="#2a2e39"
                ),
                yaxis=dict(gridcolor="#2a2e39"),
                legend=dict(orientation="h", y=1.1, x=0, font=dict(size=10))
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})

        with col_info:
            st.markdown(f"<div class='badge-macro' style='color:{align_color} !important; font-weight:bold;'>{align_txt}</div>", unsafe_allow_html=True)
            
            macro_txt = "Haussier" if macro_bull else "Baissier"
            micro_txt = "Haussier" if micro_bull else "Baissier"
            st.markdown(f"<div style='font-size:12px; margin-bottom:10px;'>Macro (Hebdo) : <b>{macro_txt}</b><br>Micro (Jour) : <b>{micro_txt}</b></div>", unsafe_allow_html=True)
            
            if score >= 20 or score <= -20:
                is_long = score >= 20
                risque = capital * (risque_pct / 100)
                dist = abs(prix - sl)
                qte = risque / dist
                
                st.markdown(f"""
                <div class="action-box">
                    <div style="font-size:12px; color:#787b86 !important; margin-bottom:5px;">Plan d'action ({'Achat' if is_long else 'Vente'})</div>
                    <div class="action-row"><span>Stop Loss</span> <span style="color:#f23645 !important; font-weight:bold;">{sl:,.2f}</span></div>
                    <div class="action-row"><span>Take Profit</span> <span style="color:#089981 !important; font-weight:bold;">{tp:,.2f}</span></div>
                    <div class="action-row" style="border:none;"><span>Quantité</span> <span style="color:#ffffff !important; font-weight:bold;">{qte:.4f}</span></div>
                    <div style="font-size:11px; margin-top:5px; color:#787b86 !important;">Risque max: {risque:.2f} $</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Aucun plan d'action. Attente de signal clair.")

            with st.expander("Détail du score"):
                for r in raisons:
                    st.write(f"- {r}")

        st.markdown(f"<div style='text-align:center; font-size:10px; color:#787b86 !important; margin-top:10px;'>Données du {df.index[-1].strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
