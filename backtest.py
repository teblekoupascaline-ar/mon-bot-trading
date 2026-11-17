import yfinance as yf
import pandas as pd
import pandas_ta_classic as ta

def analyser_actif(ticker, capital_depart=10.0):
    print(f"\n==========================================")
    print(f" 📊 ANALYSE DE : {ticker}")
    print(f"==========================================")
    
    # 1. Téléchargement des 5 dernières années de données
    print("⏳ Téléchargement des données (5 ans)...")
    df = yf.download(ticker, period="5y", interval="1d", progress=False)
    
    if df.empty:
        print("❌ Erreur: Impossible de télécharger les données.")
        return

    # Nettoyage des colonnes
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 2. Calcul des indicateurs
    df['SMA_50'] = ta.sma(df['Close'], length=50)
    df['SMA_200'] = ta.sma(df['Close'], length=200)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # On enlève les premières lignes vides (à cause des moyennes mobiles)
    df = df.dropna()

    # 3. Simulation du Bot
    position = 0.0 
    solde = capital_depart
    frais = 0.001 # 0.1% de frais par trade
    historique_valeur = []
    trades = 0
    derniere_action = "Aucune"

    for i in range(1, len(df)):
        prix_actuel = float(df['Close'].iloc[i])
        prix_precedent = float(df['Close'].iloc[i-1])

        # LOGIQUE DU BOT : 
        # Achat si le prix croise au-dessus de la SMA 50 et que le RSI n'est pas en surachat
        signal_achat = (prix_actuel > df['SMA_50'].iloc[i]) and (prix_precedent <= df['SMA_50'].iloc[i-1]) and (df['RSI'].iloc[i] < 70)
        # Vente si le prix croise en-dessous de la SMA 50
        signal_vente = (prix_actuel < df['SMA_50'].iloc[i]) and (prix_precedent >= df['SMA_50'].iloc[i-1])

        if signal_achat and solde > 0:
            # Le bot achète
            quantite = (solde * (1 - frais)) / prix_actuel
            position = quantite
            solde = 0
            trades += 1
            derniere_action = f"ACHAT le {df.index[i].strftime('%d/%m/%Y')} à {prix_actuel:.2f}$"
            
        elif signal_vente and position > 0:
            # Le bot vend
            solde = position * prix_actuel * (1 - frais)
            position = 0
            trades += 1
            derniere_action = f"VENTE le {df.index[i].strftime('%d/%m/%Y')} à {prix_actuel:.2f}$"

        # Calcul de la valeur totale du compte chaque jour
        valeur_totale = solde + (position * prix_actuel)
        historique_valeur.append(valeur_totale)

    # 4. Résultats
    valeur_finale = historique_valeur[-1] if historique_valeur else capital_depart
    gain = valeur_finale - capital_depart
    pourcentage = (gain / capital_depart) * 100

    # Calcul de la pire chute (Drawdown)
    serie_valeur = pd.Series(historique_valeur)
    pic = serie_valeur.cummax()
    drawdown = (serie_valeur - pic) / pic
    max_drawdown = drawdown.min() * 100

    print(f"💰 Capital initial : {capital_depart} $")
    print(f"💵 Valeur finale   : {valeur_finale:.2f} $")
    print(f"📈 Gain/Perte      : {gain:+.2f} $ ({pourcentage:+.2f}%)")
    print(f"🔄 Nombre de trades: {trades}")
    print(f"📉 Pire chute      : {max_drawdown:.2f}%")
    print(f"🤖 Dernier signal  : {derniere_action}")
    print("==========================================\n")

if __name__ == "__main__":
    # On lance le test sur Bitcoin et sur l'Euro/Dollar
    analyser_actif("BTC-USD", 10.0)
    analyser_actif("EURUSD=X", 10.0)