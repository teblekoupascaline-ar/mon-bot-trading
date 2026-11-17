import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(page_title="Mon Bot Trading", page_icon="📈", layout="wide")

st.title("📈 Mon Copilote de Trading")
st.write("Bienvenue fréro ! Voici l'analyse technique du jour.")

# Menu sur le côté
with st.sidebar:
    st.header("Paramètres")
    ticker = st.text_input("Ticker (ex: BTC-USD, AAPL, EURUSD=X)", "BTC-USD")
    periode = st.selectbox("Période d'analyse", ["1mo", "3mo", "6mo", "1y"], index=2)
    bouton_analyser = st.button("🔄 Analyser", type="primary")

# Fonction pour charger les données
@st.cache_data(ttl=3600) # Garde les données en mémoire 1 heure pour aller plus vite
def charger_donnees(ticker, periode):
    df = yf.download(ticker, period=periode, interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

if bouton_analyser or ticker:
    with st.spinner("Analyse en cours..."):
        df = charger_donnees(ticker, periode)
        
        if df.empty:
            st.error("Impossible de trouver ce ticker. Vérifie le nom.")
        else:
            # Calcul des indicateurs
            df['SMA_20'] = ta.sma(df['Close'], length=20)
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            df = df.dropna()
            dernier = df.iloc[-1]
            precedent = df.iloc[-2]
            
            # --- LOGIQUE DU SIGNAL ---
            score = 0
            if dernier['Close'] > dernier['SMA_50']: score += 1
            else: score -= 1
            
            if dernier['SMA_20'] > dernier['SMA_50']: score += 1
            else: score -= 1
            
            if dernier['RSI'] < 30: score += 1
            elif dernier['RSI'] > 70: score -= 1

            # Affichage des métriques
            col1, col2, col3 = st.columns(3)
            col1.metric("Prix Actuel", f"{dernier['Close']:.2f} $")
            col2.metric("RSI (14)", f"{dernier['RSI']:.1f}")
            
            if score >= 2:
                col3.success("🟢 Signal : ACHAT")
            elif score <= -2:
                col3.error("🔴 Signal : VENTE")
            else:
                col3.info("⚪ Signal : NEUTRE")
            
            # Graphique
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Prix"))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='orange', width=1.5), name="SMA 20"))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='blue', width=1.5), name="SMA 50"))
            
            fig.update_layout(height=500, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

            # Explication
            st.write("### 🧠 Pourquoi ce signal ?")
            if score >= 2:
                st.write("Le bot est haussier car le prix est au-dessus de la SMA 50, la tendance courte (SMA 20) est au-dessus de la tendance longue, et le RSI n'est pas en zone de surchauffe.")
            elif score <= -2:
                st.write("Le bot est baissier car le prix est sous la SMA 50, la tendance courte est sous la tendance longue, ou le RSI indique une chute.")
            else:
                st.write("Le marché est indécis. Les indicateurs se contredisent, il vaut mieux attendre.")