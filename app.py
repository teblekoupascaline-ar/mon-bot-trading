import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(page_title="Mon Bot Trading PRO", page_icon="🚀", layout="wide")

st.title("🚀 Mon Copilote de Trading PRO")
st.write("Analyse multi-facteurs en temps réel.")

# --- MENU SUR LE COTE ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    
    # Liste déroulante pour éviter les erreurs de frappe
    actifs = {
        "Bitcoin (BTC-USD)": "BTC-USD",
        "Ethereum (ETH-USD)": "ETH-USD",
        "Euro / Dollar (EURUSD=X)": "EURUSD=X",
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "S&P 500 (^GSPC)": "^GSPC"
    }
    choix_actif = st.selectbox("Choisir un actif :", list(actifs.keys()))
    ticker = actifs[choix_actif]
    
    # On force 1 an minimum pour que la SMA 200 fonctionne
    periode = st.selectbox("Période d'analyse", ["1y", "2y", "5y"], index=0)
    bouton_analyser = st.button("🔄 Lancer l'analyse", type="primary")

# --- CHARGEMENT DES DONNEES ---
@st.cache_data(ttl=3600)
def charger_donnees(ticker, periode):
    df = yf.download(ticker, period=periode, interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# --- LOGIQUE DU BOT ---
if bouton_analyser or ticker:
    with st.spinner("Analyse des marchés en cours..."):
        df = charger_donnees(ticker, periode)
        
        if df.empty:
            st.error("Impossible de trouver ce ticker. Vérifie le nom.")
        else:
            # Calcul des indicateurs
            df['SMA_20'] = ta.sma(df['Close'], length=20)
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            df = df.dropna()
            dernier = df.iloc[-1]
            avant_dernier = df.iloc[-2]
            
            # --- LE CERVEAU DU BOT (Score de -100 à +100) ---
            score = 0
            raisons = []
            
            # 1. Tendance de fond (SMA 200)
            if dernier['Close'] > dernier['SMA_200']:
                score += 30
                raisons.append("✅ **Tendance de fond** : Haussière (Prix au-dessus de la SMA 200).")
            else:
                score -= 30
                raisons.append("❌ **Tendance de fond** : Baissière (Prix sous la SMA 200).")
                
            # 2. Tendance court terme (SMA 20 vs SMA 50)
            if dernier['SMA_20'] > dernier['SMA_50']:
                score += 20
                raisons.append("✅ **Momentum** : Positif (SMA 20 au-dessus de la SMA 50).")
            else:
                score -= 20
                raisons.append("❌ **Momentum** : Négatif (SMA 20 sous la SMA 50).")
                
            # 3. RSI
            if dernier['RSI'] < 30:
                score += 30
                raisons.append(f"✅ **RSI** : Survente ({dernier['RSI']:.1f}) - Potentiel de rebond.")
            elif dernier['RSI'] > 70:
                score -= 30
                raisons.append(f"❌ **RSI** : Surachat ({dernier['RSI']:.1f}) - Risque de correction.")
            else:
                raisons.append(f"➖ **RSI** : Neutre ({dernier['RSI']:.1f}).")

            # --- AFFICHAGE DES METRIQUES ---
            col1, col2, col3, col4 = st.columns(4)
            variation = ((dernier['Close'] - avant_dernier['Close']) / avant_dernier['Close']) * 100
            
            col1.metric("Prix Actuel", f"{dernier['Close']:.2f}", f"{variation:+.2f}%")
            col2.metric("RSI (14)", f"{dernier['RSI']:.1f}")
            col3.metric("Plus bas (Période)", f"{df['Low'].min():.2f}")
            
            # Affichage du signal
            if score >= 50:
                col4.success(f"🟢 ACHAT FORT\n\nScore: +{score}")
            elif score > 0:
                col4.info(f"🟡 ACHAT PRUDENT\n\nScore: +{score}")
            elif score <= -50:
                col4.error(f"🔴 VENTE FORTE\n\nScore: {score}")
            elif score < 0:
                col4.warning(f"🟠 VENTE PRUDENTE\n\nScore: {score}")
            else:
                col4.info(f"⚪ NEUTRE\n\nScore: {score}")

            st.divider()

            # --- ONGLETS POUR LE DESIGN ---
            onglet_graphique, onglet_explication, onglet_donnees = st.tabs(["📈 Graphique", "🧠 Pourquoi ce score ?", "📊 Données Brutes"])
            
            with onglet_graphique:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Prix"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='orange', width=1.5), name="SMA 50"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='red', width=2), name="SMA 200"))
                fig.update_layout(height=500, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0), template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

            with onglet_explication:
                st.write("### Voici l'analyse détaillée du bot :")
                for raison in raisons:
                    st.write(raison)

            with onglet_donnees:
                st.write("### Historique des dernières séances")
                st.dataframe(df.tail(10)[['Open', 'High', 'Low', 'Close', 'RSI']], use_container_width=True)
