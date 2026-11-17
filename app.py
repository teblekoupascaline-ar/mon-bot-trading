import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(page_title="Mon Bot Trading PRO", page_icon="🚀", layout="wide")

st.title("🚀 Mon Copilote de Trading PRO")
st.write("Analyse multi-facteurs avec score de confiance.")

# Menu sur le côté
with st.sidebar:
    st.header("⚙️ Paramètres")
    ticker = st.text_input("Ticker (ex: BTC-USD, AAPL)", "BTC-USD")
    periode = st.selectbox("Période d'analyse", ["3mo", "6mo", "1y", "2y"], index=2)
    bouton_analyser = st.button("🔄 Analyser", type="primary")

@st.cache_data(ttl=3600)
def charger_donnees(ticker, periode):
    df = yf.download(ticker, period=periode, interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

if bouton_analyser or ticker:
    with st.spinner("Analyse en cours..."):
        df = charger_donnees(ticker, periode)
        
        if df.empty:
            st.error("Impossible de trouver ce ticker.")
        else:
            # Calcul des indicateurs (ajout de la SMA 200 pour la tendance de fond)
            df['SMA_20'] = ta.sma(df['Close'], length=20)
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            df = df.dropna()
            dernier = df.iloc[-1]
            
            # --- LE CERVEAU DU BOT (Système de score -100 à +100) ---
            score = 0
            raisons = []
            
            # 1. Tendance de fond (SMA 200)
            if dernier['Close'] > dernier['SMA_200']:
                score += 30
                raisons.append("✅ Tendance de fond haussière (Prix > SMA 200).")
            else:
                score -= 30
                raisons.append("❌ Tendance de fond baissière (Prix < SMA 200).")
                
            # 2. Tendance court terme (SMA 20 vs SMA 50)
            if dernier['SMA_20'] > dernier['SMA_50']:
                score += 20
                raisons.append("✅ Momentum positif (SMA 20 croise au-dessus de la SMA 50).")
            else:
                score -= 20
                raisons.append("❌ Momentum négatif (SMA 20 sous la SMA 50).")
                
            # 3. RSI (Survente / Surachat)
            if dernier['RSI'] < 30:
                score += 30
                raisons.append(f"✅ RSI en zone de survente ({dernier['RSI']:.1f}) : potentiel rebond.")
            elif dernier['RSI'] > 70:
                score -= 30
                raisons.append(f"❌ RSI en zone de surachat ({dernier['RSI']:.1f}) : risque de correction.")
            else:
                raisons.append(f"➖ RSI neutre ({dernier['RSI']:.1f}).")

            # --- Affichage des métriques ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Prix Actuel", f"{dernier['Close']:.2f} $", f"{dernier['Close'] - df['Close'].iloc[-2]:.2f}")
            col2.metric("RSI (14)", f"{dernier['RSI']:.1f}")
            
            # Interprétation du Score
            if score >= 50:
                col3.success(f"🟢 SIGNAL : ACHAT FORT (Score: +{score})")
            elif score > 0:
                col3.info(f"🟡 SIGNAL : ACHAT PRUDENT (Score: +{score})")
            elif score <= -50:
                col3.error(f"🔴 SIGNAL : VENTE FORTE (Score: {score})")
            elif score < 0:
                col3.warning(f"🟠 SIGNAL : VENTE PRUDENTE (Score: {score})")
            else:
                col3.info(f"⚪ SIGNAL : NEUTRE (Score: {score})")
            
            # Graphique
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Prix"))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='orange', width=1.5), name="SMA 50"))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='red', width=2), name="SMA 200"))
            
            fig.update_layout(height=500, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

            # --- Explication (Le fameux "Pourquoi") ---
            st.write("### 🧠 Pourquoi ce score ?")
            for raison in raisons:
                st.write(raison)
