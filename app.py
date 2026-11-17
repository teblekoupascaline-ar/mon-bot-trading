import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="Terminal Trading", layout="wide", initial_sidebar_state="collapsed")

# --- CSS SUR MESURE (TRADINGVIEW STYLE) ---
st.markdown("""
<style>
    /* Masquer les éléments inutiles de Streamlit pour gagner de la place sur mobile */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp {
        background-color: #131722; /* Fond TradingView */
        font-family: 'Inter', sans-serif;
        color: #d1d4dc !important;
    }

    /* Forcer la couleur du texte pour éviter le texte noir illisible */
    div, p, span, label {
        color: #d1d4dc !important;
    }

    /* Bandeau supérieur compact */
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
    
    .metric-box {
        text-align: center;
    }
    
    .metric-label {
        font-size: 10px;
        color: #787b86 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-value {
        font-size: 16px;
        font-weight: 800;
        color: #ffffff !important;
    }

    /* Styles des signaux */
    .signal-buy { color: #089981 !important; } /* Vert TradingView */
    .signal-sell { color: #f23645 !important; } /* Rouge TradingView */
    .signal-neutral { color: #fbc02d !important; } /* Jaune */

    /* Animation Pulse */
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
    
    .pulse-green {
        background: rgba(8, 153, 129, 0.15);
        border: 1px solid #089981;
        border-radius: 6px;
        padding: 5px 10px;
        animation: pulse-green 2s infinite;
    }
    
    .pulse-red {
        background: rgba(242, 54, 69, 0.15);
        border: 1px solid #f23645;
        border-radius: 6px;
        padding: 5px 10px;
        animation: pulse-red 2s infinite;
    }

    /* Boîte plan d'action */
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
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Paramètres")
    actifs = {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", 
        "EUR/USD": "EURUSD=X", "Apple": "AAPL", 
        "Tesla": "TSLA", "S&P 500": "^GSPC"
    }
    choix_actif = st.selectbox("Actif", list(actifs.keys()))
    ticker = actifs[choix_actif]
    periode = st.selectbox("Période", ["6mo", "1y", "2y", "5y"], index=2)
    
    st.divider()
    capital = st.number_input("Capital ($)", min_value=10.0, value=50.0, step=10.0)
    risque_pct = st.slider("Risque (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
    
    if st.button("Actualiser", type="primary"):
        st.cache_data.clear()

@st.cache_data(ttl=60)
def charger_donnees(ticker, periode):
    df = yf.download(ticker, period=periode, interval="1d", progress=False)
    df_w = yf.download(ticker, period=periode, interval="1wk", progress=False)
    for d in [df, df_w]:
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
    return df, df_w

# --- LOGIQUE PRINCIPALE ---
with st.spinner("Analyse..."):
    df, df_w = charger_donnees(ticker, periode)
    
    if not df.empty and not df_w.empty:
        # Calculs
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df = df.dropna()
        
        df_w['SMA_20'] = ta.sma(df_w['Close'], length=20)
        df_w = df_w.dropna()
        
        dernier = df.iloc[-1]
        avant = df.iloc[-2]
        dernier_w = df_w.iloc[-1]
        
        # Logique de score
        score = 0
        if dernier_w['Close'] > dernier_w['SMA_20']: score += 30
        else: score -= 30
        
        if dernier['Close'] > dernier['SMA_200']: score += 20
        else: score -= 20
            
        if dernier['RSI'] < 30: score += 20
        elif dernier['RSI'] > 70: score -= 20

        prix = dernier['Close']
        variation = ((prix - avant['Close']) / avant['Close']) * 100
        
        # Définition du signal et de la couleur
        if score >= 50:
            signal_txt, sig_class, pulse = "ACHAT FORT", "signal-buy", "pulse-green"
        elif score > 0:
            signal_txt, sig_class, pulse = "ACHAT", "signal-buy", ""
        elif score <= -50:
            signal_txt, sig_class, pulse = "VENTE FORTE", "signal-sell", "pulse-red"
        elif score < 0:
            signal_txt, sig_class, pulse = "VENTE", "signal-sell", ""
        else:
            signal_txt, sig_class, pulse = "NEUTRE", "signal-neutral", ""

        # --- BANDEAU SUPÉRIEUR COMPACT (Prix, RSI, Signal) ---
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

        # --- GRAPHIQUE ---
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], 
            name="Prix", increasing_line_color='#089981', decreasing_line_color='#f23645'
        ))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#fbc02d', width=1), name="SMA 50"))
        
        # Plan d'action
        action_html = ""
        if score >= 20 or score <= -20:
            is_long = score >= 20
            sl = prix - (dernier['ATR'] * 1.5) if is_long else prix + (dernier['ATR'] * 1.5)
            tp = prix + (dernier['ATR'] * 3.0) if is_long else prix - (dernier['ATR'] * 3.0)
            
            risque = capital * (risque_pct / 100)
            dist = abs(prix - sl)
            qte = risque / dist
            
            fig.add_hline(y=sl, line_dash="dash", line_color="#f23645", annotation_text="SL")
            fig.add_hline(y=tp, line_dash="dash", line_color="#089981", annotation_text="TP")
            
            action_html = f"""
            <div class="action-box">
                <div class="action-row"><span>Stop Loss</span> <span style="color:#f23645 !important; font-weight:bold;">{sl:,.2f}</span></div>
                <div class="action-row"><span>Take Profit</span> <span style="color:#089981 !important; font-weight:bold;">{tp:,.2f}</span></div>
                <div class="action-row" style="border:none;"><span>Quantité</span> <span style="color:#ffffff !important; font-weight:bold;">{qte:.4f}</span></div>
            </div>
            """
        else:
            action_html = '<div class="action-box" style="text-align:center; color:#787b86 !important;">Attente de signal clair</div>'

        # Configuration du graphique pour mobile (hauteur réduite, marges minimes)
        fig.update_layout(
            height=380, # Plus petit pour tenir sur l'écran
            template="plotly_dark", 
            dragmode="pan", 
            paper_bgcolor='#131722', plot_bgcolor='#131722',
            margin=dict(l=5, r=5, t=5, b=5),
            xaxis=dict(
                rangeslider=dict(visible=False), # On l'enlève sur mobile pour gagner de la place
                type="date",
                gridcolor="#2a2e39"
            ),
            yaxis=dict(gridcolor="#2a2e39"),
            legend=dict(orientation="h", y=1.1, x=0, font=dict(size=10))
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}) # On cache la barre d'outils
        
        # Affichage du plan d'action juste sous le graphique
        st.markdown(action_html, unsafe_allow_html=True)
        
        # Date
        st.markdown(f"<div style='text-align:center; font-size:10px; color:#787b86 !important; margin-top:10px;'>Données du {df.index[-1].strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
