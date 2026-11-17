import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta
import plotly.graph_objects as go

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Terminal d'Analyse", page_icon="", layout="wide")

# --- INJECTION DU CSS POUR LE DESIGN ULTRA COLOSSAL ---
st.markdown("""
<style>
    /* Importation d'une police professionnelle */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    /* Fond dégradé sombre */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e293b 0%, #0f172a 100%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Effet Glassmorphism sur les métriques */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    
    /* Style des boutons */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
        color: white;
        border: none;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        color: white;
        border: none;
    }
    
    /* Style des onglets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-bottom: 2px solid transparent;
        color: #94a3b8;
        font-weight: 600;
        padding-bottom: 8px;
    }
    
    .stTabs [aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }
    
    /* Titres */
    h1, h2, h3 {
        font-weight: 800;
        letter-spacing: -0.5px;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("Terminal d'Analyse Financière")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem;'>Système d'aide à la décision multi-timeframes et gestion des risques.</p>", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Paramètres du Système")
    
    actifs = {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Euro / Dollar (EURUSD)": "EURUSD=X",
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "S&P 500 (^GSPC)": "^GSPC"
    }
    choix_actif = st.selectbox("Sélectionner l'actif", list(actifs.keys()))
    ticker = actifs[choix_actif]
    
    periode = st.selectbox("Horizon temporel des données", ["1y", "2y", "5y"], index=1)
    
    st.divider()
    st.header("Gestion du Capital")
    capital = st.number_input("Capital total (USD)", min_value=10.0, value=100.0, step=10.0)
    risque_pct = st.slider("Risque alloué par trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5, help="Règle de gestion : ne jamais risquer plus de 1 à 2% de son capital par position.")
    
    bouton_analyser = st.button("Actualiser l'analyse")

# --- LOGIQUE DE DONNEES ---
@st.cache_data(ttl=60)
def charger_donnees(ticker, periode):
    df_daily = yf.download(ticker, period=periode, interval="1d", progress=False)
    df_weekly = yf.download(ticker, period=periode, interval="1wk", progress=False)
    
    for df in [df_daily, df_weekly]:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
    return df_daily, df_weekly

if bouton_analyser:
    st.cache_data.clear()

with st.spinner("Extraction des données et calcul des indicateurs..."):
    df, df_weekly = charger_donnees(ticker, periode)
    
    if df.empty or df_weekly.empty:
        st.error("Données introuvables pour cet actif.")
    else:
        # Indicateurs
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df = df.dropna()
        
        df_weekly['SMA_20'] = ta.sma(df_weekly['Close'], length=20)
        df_weekly = df_weekly.dropna()
        
        dernier = df.iloc[-1]
        avant_dernier = df.iloc[-2]
        dernier_weekly = df_weekly.iloc[-1]
        
        # --- ANALYSE MULTI-TIMEFRAMES ---
        st.markdown("### Analyse de Tendance Multi-Timeframe")
        
        if dernier_weekly['Close'] > dernier_weekly['SMA_20']:
            tendance_hebdo, score_hebdo = "Haussière (Macro)", 1
        else:
            tendance_hebdo, score_hebdo = "Baissière (Macro)", -1
            
        if dernier['SMA_20'] > dernier['SMA_50']:
            tendance_jour, score_jour = "Haussière (Micro)", 1
        else:
            tendance_jour, score_jour = "Baissière (Micro)", -1

        col_macro, col_micro = st.columns(2)
        col_macro.metric("Tendance de fond (Hebdomadaire)", tendance_hebdo, delta="SMA 20" if score_hebdo == 1 else "- SMA 20", delta_color="normal" if score_hebdo == 1 else "inverse")
        col_micro.metric("Tendance actuelle (Quotidienne)", tendance_jour, delta="SMA 20 > SMA 50" if score_jour == 1 else "- SMA 20 < SMA 50", delta_color="normal" if score_jour == 1 else "inverse")

        if score_hebdo == 1 and score_jour == 1:
            st.success("Alignement Haussier : La tendance macro et micro sont synchronisées à la hausse. Les signaux d'achat sont privilégiés.")
            alignement_score = 30
        elif score_hebdo == -1 and score_jour == -1:
            st.error("Alignement Baissier : La tendance macro et micro sont synchronisées à la baisse. Les signaux de vente sont privilégiés.")
            alignement_score = -30
        else:
            st.warning("Conflit de tendances : La macro et la micro ne sont pas alignées. Le système recommande l'attente.")
            alignement_score = 0

        st.divider()

        # --- SCORE GLOBAL ---
        score = alignement_score
        raisons = [f"Analyse Multi-Timeframes : {'Alignement' if alignement_score != 0 else 'Conflit'} ({alignement_score} points)"]

        if dernier['Close'] > dernier['SMA_200']:
            score += 20
            raisons.append("Tendance de fond (Daily) : Prix au-dessus de la SMA 200 (Haussier).")
        else:
            score -= 20
            raisons.append("Tendance de fond (Daily) : Prix en-dessous de la SMA 200 (Baissier).")
            
        if dernier['RSI'] < 30:
            score += 20
            raisons.append(f"RSI : Zone de survente ({dernier['RSI']:.1f}).")
        elif dernier['RSI'] > 70:
            score -= 20
            raisons.append(f"RSI : Zone de surachat ({dernier['RSI']:.1f}).")
        else:
            raisons.append(f"RSI : Zone neutre ({dernier['RSI']:.1f}).")

        # --- METRIQUES ET SIGNAL ---
        col1, col2, col3, col4 = st.columns(4)
        prix_actuel = dernier['Close']
        variation = ((prix_actuel - avant_dernier['Close']) / avant_dernier['Close']) * 100
        
        col1.metric("Prix Actuel", f"{prix_actuel:.2f}", f"{variation:+.2f}%")
        col2.metric("RSI (14)", f"{dernier['RSI']:.1f}")
        col3.metric("Volatilité (ATR)", f"{dernier['ATR']:.2f}")
        
        if score >= 50:
            col4.metric("Signal Système", "Achat Fort", f"Score: +{score}")
        elif score > 0:
            col4.metric("Signal Système", "Achat Prudent", f"Score: +{score}")
        elif score <= -50:
            col4.metric("Signal Système", "Vente Forte", f"Score: {score}")
        elif score < 0:
            col4.metric("Signal Système", "Vente Prudente", f"Score: {score}")
        else:
            col4.metric("Signal Système", "Neutre", f"Score: {score}")

        st.divider()

        # --- PLAN D'ACTION ET CALCULATEUR ---
        if score >= 20:
            st.markdown("### Plan d'Action : Position Longue (Achat)")
            stop_loss = prix_actuel - (dernier['ATR'] * 1.5)
            take_profit = prix_actuel + (dernier['ATR'] * 3.0)
            
            risque_absolu = capital * (risque_pct / 100)
            distance_sl = prix_actuel - stop_loss
            quantite = risque_absolu / distance_sl
            valeur_position = quantite * prix_actuel
            
            col_sl, col_tp = st.columns(2)
            col_sl.metric("Stop Loss (SL)", f"{stop_loss:.2f}", "Seuil de protection", delta_color="inverse")
            col_tp.metric("Take Profit (TP)", f"{take_profit:.2f}", "Objectif de gain", delta_color="normal")
            
            st.info(f"**Recommandation d'exécution :**\n"
                    f"- Quantité à acquérir : **{quantite:.4f} unités**\n"
                    f"- Valeur de la position : **{valeur_position:.2f} USD**\n"
                    f"- Risque maximal (si SL touché) : **{risque_absolu:.2f} USD** ({risque_pct}% du capital)")
            
            if valeur_position > capital:
                st.warning("Alerte : Cette position nécessite un effet de levier (Leverage) ou une réduction du risque car elle dépasse votre capital total.")
        
        elif score <= -20:
            st.markdown("### Plan d'Action : Position Courte (Vente / Short)")
            stop_loss = prix_actuel + (dernier['ATR'] * 1.5)
            take_profit = prix_actuel - (dernier['ATR'] * 3.0)
            
            risque_absolu = capital * (risque_pct / 100)
            distance_sl = stop_loss - prix_actuel
            quantite = risque_absolu / distance_sl
            valeur_position = quantite * prix_actuel
            
            col_sl, col_tp = st.columns(2)
            col_sl.metric("Stop Loss (SL)", f"{stop_loss:.2f}", "Seuil de protection", delta_color="inverse")
            col_tp.metric("Take Profit (TP)", f"{take_profit:.2f}", "Objectif de gain", delta_color="normal")
            
            st.info(f"**Recommandation d'exécution :**\n"
                    f"- Quantité à vendre (Short) : **{quantite:.4f} unités**\n"
                    f"- Valeur de la position : **{valeur_position:.2f} USD**\n"
                    f"- Risque maximal (si SL touché) : **{risque_absolu:.2f} USD** ({risque_pct}% du capital)")
            
            if valeur_position > capital:
                st.warning("Alerte : Cette position nécessite un effet de levier (Leverage) car elle dépasse votre capital total.")
        
        else:
            st.info("Aucun plan d'action défini. Les conditions de marché ne sont pas optimales. Attendez un signal clair.")

        st.divider()

        # --- ONGLETS GRAPHIQUE ET ANALYSE ---
        onglet_graphique, onglet_explication = st.tabs(["Graphique Interactif", "Détail de l'Analyse"])
        
        with onglet_graphique:
            fig = go.Figure()
            # Chandeliers
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], 
                name="Prix", 
                increasing_line_color='#38bdf8', decreasing_line_color='#f43f5e'
            ))
            # Moyennes mobiles
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#fbbf24', width=1.5), name="SMA 50"))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='#a855f7', width=2), name="SMA 200"))
            
            # Lignes SL/TP
            if score >= 20 or score <= -20:
                fig.add_hline(y=stop_loss, line_dash="dot", line_color="#f43f5e", annotation_text="Stop Loss")
                fig.add_hline(y=take_profit, line_dash="dot", line_color="#10b981", annotation_text="Take Profit")

            fig.update_layout(
                height=550, 
                template="plotly_dark", 
                dragmode="pan", # Mode déplacement fluide
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1M", step="month", stepmode="backward"),
                            dict(count=3, label="3M", step="month", stepmode="backward"),
                            dict(count=6, label="6M", step="month", stepmode="backward"),
                            dict(count=1, label="1A", step="year", stepmode="backward"),
                            dict(step="all", label="Max")
                        ]),
                        bgcolor="rgba(30, 41, 59, 0.8)"
                    ),
                    rangeslider=dict(visible=True, bgcolor="rgba(30, 41, 59, 0.5)"), 
                    type="date"
                ),
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            date_derniere_bougie = df.index[-1].strftime('%d/%m/%Y')
            st.caption(f"Source des données : Yahoo Finance. Dernière actualisation : {date_derniere_bougie}.")

        with onglet_explication:
            st.markdown("### Justification du Score")
            for raison in raisons:
                st.markdown(f"- {raison}")
