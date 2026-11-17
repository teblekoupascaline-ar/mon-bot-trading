import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import plotly.graph_objects as go

st.set_page_config(page_title="Mon Bot Trading PRO", page_icon="🚀", layout="wide")

st.title("🚀 Mon Copilote de Trading PRO")
st.write("Analyse multi-timeframes avec calcul de risque intégré.")

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
    
    periode = st.selectbox("Période d'analyse", ["1y", "2y", "5y"], index=1)
    bouton_analyser = st.button("🔄 Lancer l'analyse", type="primary")

@st.cache_data(ttl=3600)
def charger_donnees(ticker, periode):
    # Données Quotidiennes
    df_daily = yf.download(ticker, period=periode, interval="1d", progress=False)
    # Données Hebdomadaires
    df_weekly = yf.download(ticker, period=periode, interval="1wk", progress=False)
    
    for df in [df_daily, df_weekly]:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
    return df_daily, df_weekly

if bouton_analyser or ticker:
    with st.spinner("Analyse Multi-Timeframes en cours..."):
        df, df_weekly = charger_donnees(ticker, periode)
        
        if df.empty or df_weekly.empty:
            st.error("Impossible de trouver ce ticker.")
        else:
            # --- CALCUL INDICATEURS QUOTIDIENS ---
            df['SMA_20'] = ta.sma(df['Close'], length=20)
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
            df = df.dropna()
            
            # --- CALCUL INDICATEURS HEBDO (SMA 20) ---
            df_weekly['SMA_20'] = ta.sma(df_weekly['Close'], length=20)
            df_weekly = df_weekly.dropna()
            
            dernier = df.iloc[-1]
            avant_dernier = df.iloc[-2]
            dernier_weekly = df_weekly.iloc[-1]
            
            # --- 1. ANALYSE MULTI-TIMEFRAMES ---
            st.subheader("🌍 Alignement des Tendances")
            
            # Tendance Hebdo (Macro)
            if dernier_weekly['Close'] > dernier_weekly['SMA_20']:
                tendance_hebdo = "HAUSSIÈRE"
                couleur_hebdo = "green"
                score_hebdo = 1
            else:
                tendance_hebdo = "BAISSIÈRE"
                couleur_hebdo = "red"
                score_hebdo = -1
                
            # Tendance Quotidienne (Micro)
            if dernier['SMA_20'] > dernier['SMA_50']:
                tendance_jour = "HAUSSIÈRE"
                couleur_jour = "green"
                score_jour = 1
            else:
                tendance_jour = "BAISSIÈRE"
                couleur_jour = "red"
                score_jour = -1

            col_macro, col_micro = st.columns(2)
            col_macro.metric("Tendance Hebdomadaire (Fond)", tendance_hebdo, delta="SMA 20 Hebdo" if score_hebdo == 1 else "- SMA 20 Hebdo", delta_color="normal" if score_hebdo == 1 else "inverse")
            col_micro.metric("Tendance Quotidienne (Actuelle)", tendance_jour, delta="SMA 20 > SMA 50" if score_jour == 1 else "- SMA 20 < SMA 50", delta_color="normal" if score_jour == 1 else "inverse")

            # Verdict de l'alignement
            if score_hebdo == 1 and score_jour == 1:
                st.success("🟢 **ALIGNEMENT PARFAIT (Haussier)** : La tendance de fond et la tendance actuelle montent. Les signaux d'achat sont fiables.")
                alignement_score = 30
            elif score_hebdo == -1 and score_jour == -1:
                st.error("🔴 **ALIGNEMENT PARFAIT (Baissier)** : La tendance de fond et la tendance actuelle baissent. Les signaux de vente sont fiables.")
                alignement_score = -30
            else:
                st.warning("⚠️ **CONFLIT DE TENDANCES** : Les deux périodes ne sont pas d'accord. C'est un piège classique ! Le bot te conseille d'attendre.")
                alignement_score = 0

            st.divider()

            # --- 2. LE SCORE GLOBAL ---
            score = alignement_score
            raisons = []
            raisons.append(f"**Multi-Timeframes** : {'Alignement' if alignement_score != 0 else 'Conflit'} ({alignement_score} pts)")

            # Tendance de fond (SMA 200)
            if dernier['Close'] > dernier['SMA_200']:
                score += 20
                raisons.append("✅ **Tendance de fond (Daily)** : Haussière (Prix > SMA 200).")
            else:
                score -= 20
                raisons.append("❌ **Tendance de fond (Daily)** : Baissière (Prix < SMA 200).")
                
            # RSI
            if dernier['RSI'] < 30:
                score += 20
                raisons.append(f"✅ **RSI** : Survente ({dernier['RSI']:.1f}).")
            elif dernier['RSI'] > 70:
                score -= 20
                raisons.append(f"❌ **RSI** : Surachat ({dernier['RSI']:.1f}).")
            else:
                raisons.append(f"➖ **RSI** : Neutre ({dernier['RSI']:.1f}).")

            # --- 3. AFFICHAGE METRIQUES ---
            col1, col2, col3, col4 = st.columns(4)
            prix_actuel = dernier['Close']
            variation = ((prix_actuel - avant_dernier['Close']) / avant_dernier['Close']) * 100
            
            col1.metric("Prix Actuel", f"{prix_actuel:.2f}", f"{variation:+.2f}%")
            col2.metric("RSI (14)", f"{dernier['RSI']:.1f}")
            col3.metric("ATR (Volatilité)", f"{dernier['ATR']:.2f}")
            
            # On n'autorise un vrai signal que si le score est fort
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

            # --- 4. PLAN D'ACTION ---
            if score >= 20: # On ne prend que les signaux clairs
                st.subheader("🎯 Plan d'Action (Achat)")
                stop_loss = prix_actuel - (dernier['ATR'] * 1.5)
                take_profit = prix_actuel + (dernier['ATR'] * 3.0)
                
                col_sl, col_tp = st.columns(2)
                col_sl.error(f"🛑 **Stop Loss suggéré : {stop_loss:.2f}**")
                col_tp.success(f"💰 **Take Profit suggéré : {take_profit:.2f}**")
            
            elif score <= -20:
                st.subheader("🎯 Plan d'Action (Vente à découvert)")
                stop_loss = prix_actuel + (dernier['ATR'] * 1.5)
                take_profit = prix_actuel - (dernier['ATR'] * 3.0)
                
                col_sl, col_tp = st.columns(2)
                col_sl.error(f"🛑 **Stop Loss suggéré : {stop_loss:.2f}**")
                col_tp.success(f"💰 **Take Profit suggéré : {take_profit:.2f}**")
            
            else:
                st.info("⚪ **Aucun plan d'action défini** : Les conditions ne sont pas réunies pour prendre un risque.")

            st.divider()

            # --- 5. ONGLETS ---
            onglet_graphique, onglet_explication = st.tabs(["📈 Graphique", "🧠 Analyse"])
            
            with onglet_graphique:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Prix"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='orange', width=1.5), name="SMA 50"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='red', width=2), name="SMA 200"))
                
                if score >= 20 or score <= -20:
                    fig.add_hline(y=stop_loss, line_dash="dash", line_color="red", annotation_text="Stop Loss")
                    fig.add_hline(y=take_profit, line_dash="dash", line_color="green", annotation_text="Take Profit")

                                # ... (le début de ton graphique reste pareil) ...
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='orange', width=1.5), name="SMA 50"))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='red', width=2), name="SMA 200"))
                
                if score >= 20 or score <= -20:
                    fig.add_hline(y=stop_loss, line_dash="dash", line_color="red", annotation_text="Stop Loss")
                    fig.add_hline(y=take_profit, line_dash="dash", line_color="green", annotation_text="Take Profit")

                # --- C'EST ICI QU'ON ACTIVE LE ZOOM ET LE SCROLL ---
                fig.update_layout(
                    height=500, 
                    template="plotly_dark",
                    # On active la souris pour glisser le graphique
                    dragmode="pan", 
                    # On configure la navigation
                    xaxis=dict(
                        rangeselector=dict(
                            buttons=list([
                                dict(count=1, label="1m", step="month", stepmode="backward"),
                                dict(count=3, label="3m", step="month", stepmode="backward"),
                                dict(count=6, label="6m", step="month", stepmode="backward"),
                                dict(count=1, label="1a", step="year", stepmode="backward"),
                                dict(step="all", label="Tout")
                            ])
                        ),
                        rangeslider=dict(visible=True), # La petite barre de scroll en bas
                        type="date"
                    )
                )
                st.plotly_chart(fig, use_container_width=True),
                                # (Juste en dessous de st.plotly_chart)
                date_derniere_bougie = df.index[-1].strftime('%d/%m/%Y')
                st.caption(f"🕒 Dernière donnée disponible : **{date_derniere_bougie}** (Source : Yahoo Finance). Les données sont actualisées à chaque clôture.")

            with onglet_explication:
                for raison in raisons:
                    st.write(raison)
