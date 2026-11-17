import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import plotly.graph_objects as go

st.set_page_config(page_title="Mon Bot Trading PRO", page_icon="🚀", layout="wide")

st.title("🚀 Mon Copilote de Trading PRO")
st.write("Analyse multi-facteurs avec calcul de Stop Loss et Take Profit.")

with st.sidebar:
    st.header("⚙️ Paramètres")
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
    
    periode = st.selectbox("Période d'analyse", ["1y", "2y", "5y"], index=0)
    bouton_analyser = st.button("🔄 Lancer l'analyse", type="primary")

@st.cache_data(ttl=3600)
def charger_donnees(ticker, periode):
    df = yf.download(ticker, period=periode, interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

if bouton_analyser or ticker:
    with st.spinner("Analyse des marchés et calcul des risques..."):
        df = charger_donnees(ticker, periode)
        
        if df.empty:
            st.error("Impossible de trouver ce ticker.")
        else:
            # Calcul des indicateurs
            df['SMA_20'] = ta.sma(df['Close'], length=20)
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14) # Nouvel indicateur !
            
            df = df.dropna()
            dernier = df.iloc[-1]
            avant_dernier = df.iloc[-2]
            
            # --- CERVEAU DU BOT ---
            score = 0
            raisons = []
            
            if dernier['Close'] > dernier['SMA_200']:
                score += 30
                raisons.append("✅ **Tendance de fond** : Haussière (Prix > SMA 200).")
            else:
                score -= 30
                raisons.append("❌ **Tendance de fond** : Baissière (Prix < SMA 200).")
                
            if dernier['SMA_20'] > dernier['SMA_50']:
                score += 20
                raisons.append("✅ **Momentum** : Positif (SMA 20 > SMA 50).")
            else:
                score -= 20
                raisons.append("❌ **Momentum** : Négatif (SMA 20 < SMA 50).")
                
            if dernier['RSI'] < 30:
                score += 30
                raisons.append(f"✅ **RSI** : Survente ({dernier['RSI']:.1f}).")
            elif dernier['RSI'] > 70:
                score -= 30
                raisons.append(f"❌ **RSI** : Surachat ({dernier['RSI']:.1f}).")
            else:
                raisons.append(f"➖ **RSI** : Neutre ({dernier['RSI']:.1f}).")

            # --- AFFICHAGE DES METRIQUES ---
            col1, col2, col3, col4 = st.columns(4)
            prix_actuel = dernier['Close']
            variation = ((prix_actuel - avant_dernier['Close']) / avant_dernier['Close']) * 100
            
            col1.metric("Prix Actuel", f"{prix_actuel:.2f}", f"{variation:+.2f}%")
            col2.metric("RSI (14)", f"{dernier['RSI']:.1f}")
            col3.metric("ATR (Volatilité)", f"{dernier['ATR']:.2f}")
            
            if score >= 50:
                col4.success(f"🟢 ACHAT FORT (Score: +{score})")
            elif score > 0:
                col4.info(f"🟡 ACHAT PRUDENT (Score: +{score})")
            elif score <= -50:
                col4.error(f"🔴 VENTE FORTE (Score: {score})")
            elif score < 0:
                col4.warning(f"🟠 VENTE PRUDENTE (Score: {score})")
            else:
                col4.info(f"⚪ NEUTRE (Score: {score})")

            st.divider()

            # --- CALCUL DU STOP LOSS ET TAKE PROFIT ---
            if score > 0:
                st.subheader("🎯 Plan d'Action (Achat)")
                # Stop loss à 1.5x ATR en dessous, TP à 3x ATR au dessus
                stop_loss = prix_actuel - (dernier['ATR'] * 1.5)
                take_profit = prix_actuel + (dernier['ATR'] * 3.0)
                
                col_sl, col_tp = st.columns(2)
                col_sl.error(f"🛑 **Stop Loss suggéré : {stop_loss:.2f}**\n\n(Place ton alerte ici pour limiter les pertes)")
                col_tp.success(f"💰 **Take Profit suggéré : {take_profit:.2f}**\n\n(Objectif de gain avec un ratio Risque/Récompense de 1:2)")
            
            elif score < 0:
                st.subheader("🎯 Plan d'Action (Vente à découvert / Short)")
                # Pour une vente, le stop loss est au-dessus, et le TP en dessous
                stop_loss = prix_actuel + (dernier['ATR'] * 1.5)
                take_profit = prix_actuel - (dernier['ATR'] * 3.0)
                
                col_sl, col_tp = st.columns(2)
                col_sl.error(f"🛑 **Stop Loss suggéré : {stop_loss:.2f}**\n\n(Si le prix monte au-dessus, tu coupes)")
                col_tp.success(f"💰 **Take Profit suggéré : {take_profit:.2f}**\n\n(Objectif de baisse)")
            
            else:
                st.info("⚪ **Signal Neutre** : Pas de plan d'action défini. Mieux vaut attendre que le marché se décide.")

            st.divider()

            # --- ONGLETS ---
            onglet_graphique, onglet_explication, onglet_donnees = st.tabs(["📈 Graphique", "🧠 Analyse", "📊 Données"])
            
            with onglet_graphique:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Prix"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='orange', width=1.5), name="SMA 50"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='red', width=2), name="SMA 200"))
                
                # Ajout des lignes SL et TP sur le graphique si signal
                if score > 0 or score < 0:
                    fig.add_hline(y=stop_loss, line_dash="dash", line_color="red", annotation_text="Stop Loss")
                    fig.add_hline(y=take_profit, line_dash="dash", line_color="green", annotation_text="Take Profit")
                    fig.add_hline(y=prix_actuel, line_dash="dot", line_color="blue", annotation_text="Prix Actuel")

                fig.update_layout(height=500, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=30, b=0), template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

            with onglet_explication:
                st.write("### Voici l'analyse détaillée du bot :")
                for raison in raisons:
                    st.write(raison)

            with onglet_donnees:
                st.dataframe(df.tail(10)[['Open', 'High', 'Low', 'Close', 'RSI', 'ATR']], use_container_width=True)
