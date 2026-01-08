# Documentation Technique Complète pour Bot de Trading Algorithmique

## Actions (Stocks) & Cryptomonnaies | Day Trading & Swing Trading

Ce document fournit toutes les formules mathématiques, paramètres recommandés et conditions algorithmiques pour l'implémentation d'un système de trading automatisé complet.

---

# PARTIE 1 : ANALYSE TECHNIQUE — INDICATEURS AVEC FORMULES COMPLÈTES

## 1.1 Moyennes Mobiles

### Simple Moving Average (SMA)
```
SMA(n) = (P₁ + P₂ + P₃ + ... + Pₙ) / n
```
Où **P** = prix de clôture, **n** = nombre de périodes.

### Exponential Moving Average (EMA)
```
EMA_t = Price_t × α + EMA_{t-1} × (1 - α)
α (facteur de lissage) = 2 / (n + 1)
```
**Initialisation** : EMA₁ = SMA des n premières périodes.

### Weighted Moving Average (WMA)
```
WMA = (P₁ × n + P₂ × (n-1) + ... + Pₙ × 1) / [n(n+1)/2]
```

### Double Exponential Moving Average (DEMA)
```
DEMA = 2 × EMA(n) - EMA(EMA(n))
```
Créé par Patrick Mulloy (1994). Réduit le lag par rapport à l'EMA simple.

### Triple Exponential Moving Average (TEMA)
```
EMA1 = EMA(Price, n)
EMA2 = EMA(EMA1, n)
EMA3 = EMA(EMA2, n)
TEMA = 3 × EMA1 - 3 × EMA2 + EMA3
```

**Paramètres recommandés** :

| Contexte | SMA | EMA | DEMA/TEMA |
|----------|-----|-----|-----------|
| Day Trading Stocks | 9, 20, 50 | 8, 13, 21 | 5-13 |
| Swing Trading Stocks | 20, 50, 200 | 12, 26, 50 | 13-26 |
| Day Trading Crypto | 7, 14, 25 | 7, 12, 21 | 5-12 |
| Swing Trading Crypto | 14, 30, 100 | 10, 21, 55 | 10-21 |

---

## 1.2 RSI (Relative Strength Index)

### Formule complète (J. Welles Wilder, 1978)
```
RSI = 100 - (100 / (1 + RS))
RS = Average Gain / Average Loss
```

**Calcul détaillé** :
```
Change(t) = Close(t) - Close(t-1)
Gain(t) = max(Change(t), 0)
Loss(t) = |min(Change(t), 0)|

Lissage de Wilder (méthode originale) :
Average Gain(t) = ((Average Gain(t-1) × (n-1)) + Current Gain) / n
Average Loss(t) = ((Average Loss(t-1) × (n-1)) + Current Loss) / n
```

**Cas limites** :
- Si Average Loss = 0 → RSI = 100
- Si Average Gain = 0 → RSI = 0

**Détection de divergence** :
```
Divergence haussière : Price(t) < Price(t-n) ET RSI(t) > RSI(t-n)
Divergence baissière : Price(t) > Price(t-n) ET RSI(t) < RSI(t-n)
```

**Paramètres** :

| Contexte | Période | Suracheté | Survendu |
|----------|---------|-----------|----------|
| Standard | 14 | 70 | 30 |
| Day Trading | 7-9 | 70-80 | 20-30 |
| Crypto (volatilité) | 7-10 | 75-80 | 20-25 |
| RSI-2 (court terme) | 2 | 80-90 | 10-20 |

---

## 1.3 MACD (Moving Average Convergence Divergence)

### Formules complètes (Gerald Appel)
```
Ligne MACD = EMA(12) - EMA(26)
Ligne Signal = EMA(MACD, 9)
Histogramme = Ligne MACD - Ligne Signal
```

**Calcul EMA** :
```
K₁₂ = 2 / (12 + 1) = 0.1538
K₂₆ = 2 / (26 + 1) = 0.0741
K₉ = 2 / (9 + 1) = 0.2
```

**Conditions de signal** :
```python
ACHAT = MACD croise au-dessus de Signal
VENTE = MACD croise en-dessous de Signal
CONFIRMATION_HAUSSIÈRE = MACD croise au-dessus de 0
CONFIRMATION_BAISSIÈRE = MACD croise en-dessous de 0
```

**Paramètres alternatifs** :

| Contexte | Fast | Slow | Signal |
|----------|------|------|--------|
| Standard | 12 | 26 | 9 |
| Day Trading | 5-8 | 13-21 | 1-5 |
| Crypto | 8 | 21 | 5 |
| Moins sensible | 19 | 39 | 9 |

---

## 1.4 Bandes de Bollinger

### Formules complètes
```
Bande Médiane = SMA(Close, n)
σ = √(Σ(Close_i - SMA)² / n)
Bande Supérieure = SMA(n) + (k × σ)
Bande Inférieure = SMA(n) - (k × σ)
```

**Indicateurs dérivés** :
```
Bandwidth = (Bande Supérieure - Bande Inférieure) / Bande Médiane
%B = (Prix - Bande Inférieure) / (Bande Supérieure - Bande Inférieure)
```

**Interprétation %B** :
- %B = 1.0 : Prix sur bande supérieure
- %B = 0.5 : Prix sur bande médiane
- %B = 0.0 : Prix sur bande inférieure
- %B > 1.0 : Breakout haussier
- %B < 0.0 : Breakdown baissier

**Paramètres** :

| Contexte | Période (n) | Écart-type (k) |
|----------|-------------|----------------|
| Standard | 20 | 2.0 |
| Day Trading | 10 | 1.5 |
| Long terme | 50 | 2.5 |
| Crypto (volatile) | 20 | 2.5-3.0 |

---

## 1.5 Stochastique (Stochastic Oscillator)

### Formules (George Lane)
```
%K (Fast) = ((Close - Lowest Low(n)) / (Highest High(n) - Lowest Low(n))) × 100
%D = SMA(%K, m)
```

**Trois versions** :
```
Fast Stochastic : %K brut, %D = SMA(%K, 3)
Slow Stochastic : Slow %K = Fast %D, Slow %D = SMA(Slow %K, 3)
Full Stochastic : Paramètres personnalisables (n, %K smoothing, %D smoothing)
```

**Paramètres** :

| Contexte | Période | %K Lissage | %D Lissage | Suracheté | Survendu |
|----------|---------|------------|------------|-----------|----------|
| Standard | 14 | 3 | 3 | 80 | 20 |
| Day Trading | 5-9 | 3 | 3 | 80 | 20 |
| Crypto | 10 | 5 | 5 | 85 | 15 |

---

## 1.6 ATR (Average True Range)

### Formule complète (J. Welles Wilder)
```
True Range = MAX(
    High - Low,
    |High - Close_précédent|,
    |Low - Close_précédent|
)

ATR_initial = Moyenne des n premiers TR
ATR_t = ((ATR_{t-1} × (n-1)) + TR_t) / n
```

**Applications algorithmiques** :
```
Stop-Loss = Prix d'entrée - (ATR × Multiplicateur)
Position Size = Montant Risque / (ATR × Multiplicateur)
Breakout = Close > (Close_précédent + ATR × 1.5)
```

**Multiplicateurs recommandés** :

| Condition de marché | Multiplicateur |
|---------------------|----------------|
| Faible volatilité | 1.0-1.5× |
| Normal | 2.0-2.5× |
| Haute volatilité | 3.0-4.0× |
| Crypto | 2.5-4.0× |

---

## 1.7 ADX (Average Directional Index)

### Calcul complet étape par étape

**Étape 1 : Mouvement Directionnel**
```
Up_Move = High_actuel - High_précédent
Down_Move = Low_précédent - Low_actuel

+DM = Up_Move si (Up_Move > Down_Move ET Up_Move > 0), sinon 0
-DM = Down_Move si (Down_Move > Up_Move ET Down_Move > 0), sinon 0
```

**Étape 2 : Lissage de Wilder (14 périodes)**
```
TR₁₄_actuel = TR₁₄_précédent - (TR₁₄_précédent / 14) + TR_actuel
+DM₁₄_actuel = +DM₁₄_précédent - (+DM₁₄_précédent / 14) + +DM_actuel
-DM₁₄_actuel = -DM₁₄_précédent - (-DM₁₄_précédent / 14) + -DM_actuel
```

**Étape 3 : Indicateurs Directionnels**
```
+DI₁₄ = (+DM₁₄ lissé / TR₁₄ lissé) × 100
-DI₁₄ = (-DM₁₄ lissé / TR₁₄ lissé) × 100
```

**Étape 4 : DX et ADX**
```
DX = (|+DI₁₄ - -DI₁₄| / (+DI₁₄ + -DI₁₄)) × 100
ADX = ((ADX_précédent × 13) + DX_actuel) / 14
```

**Interprétation** :

| Valeur ADX | Force de tendance | Action |
|------------|-------------------|--------|
| < 20 | Faible/Pas de tendance | Éviter trend-following |
| 20-25 | Tendance émergente | Préparer entrée |
| 25-50 | Tendance forte | Suivre la tendance |
| > 50 | Tendance très forte | Trailing stops |

---

## 1.8 Ichimoku Cloud (Kinko Hyo)

### Les 5 composantes
```
Tenkan-sen (Conversion) = (Plus Haut 9 périodes + Plus Bas 9 périodes) / 2
Kijun-sen (Base) = (Plus Haut 26 périodes + Plus Bas 26 périodes) / 2
Senkou Span A = (Tenkan-sen + Kijun-sen) / 2 [projeté 26 périodes en avant]
Senkou Span B = (Plus Haut 52 périodes + Plus Bas 52 périodes) / 2 [projeté 26 périodes en avant]
Chikou Span = Close actuel [tracé 26 périodes en arrière]
```

**Kumo (Nuage)** :
```
Nuage Haussier = Senkou Span A > Senkou Span B
Nuage Baissier = Senkou Span B > Senkou Span A
```

**Paramètres** :

| Composante | Standard (Stocks) | Crypto Adaptation |
|------------|-------------------|-------------------|
| Tenkan-sen | 9 | 10-20 |
| Kijun-sen | 26 | 30-60 |
| Senkou Span B | 52 | 60-120 |
| Décalage | 26 | 30 |

**Signaux algorithmiques** :
```python
ACHAT_FORT = (Price > Nuage) AND (Tenkan > Kijun) AND (Chikou > Price_26_ago) AND (Nuage vert)
VENTE_FORTE = (Price < Nuage) AND (Tenkan < Kijun) AND (Chikou < Price_26_ago) AND (Nuage rouge)
```

---

## 1.9 Parabolic SAR

### Formule complète
```
SAR_demain = SAR_aujourd'hui + AF × (EP - SAR_aujourd'hui)
```

**Variables** :
- **SAR** : Stop And Reverse
- **AF** : Acceleration Factor (démarre à 0.02, incrémente de 0.02, max 0.20)
- **EP** : Extreme Point (plus haut en tendance haussière, plus bas en baissière)

**Règles de mise à jour AF** :
```python
if nouveau_point_extreme_atteint:
    AF = min(AF + 0.02, 0.20)
else:
    AF = AF  # inchangé
```

**Contrainte SAR** :
```python
# Tendance haussière : SAR ne peut pas dépasser les deux derniers lows
if tendance == "HAUSSIÈRE":
    SAR = min(SAR, Low_hier, Low_avant-hier)

# Tendance baissière : SAR ne peut pas descendre sous les deux derniers highs
if tendance == "BAISSIÈRE":
    SAR = max(SAR, High_hier, High_avant-hier)
```

**Paramètres** :

| Style | AF Start | AF Increment | AF Max |
|-------|----------|--------------|--------|
| Standard | 0.02 | 0.02 | 0.20 |
| Swing Trading | 0.01 | 0.01 | 0.10 |
| Crypto | 0.02 | 0.02 | 0.25 |

---

## 1.10 Indicateurs de Volume

### OBV (On-Balance Volume)
```
OBV_actuel = OBV_précédent + {
    +Volume si Close > Close_précédent
    0 si Close = Close_précédent
    -Volume si Close < Close_précédent
}
```

### VWAP (Volume Weighted Average Price)
```
VWAP = Σ(Typical Price × Volume) / Σ(Volume)
Typical Price = (High + Low + Close) / 3
```

**Bandes VWAP** :
```
Variance = Σ[(Price - VWAP)² × Volume] / Σ(Volume)
Bande Supérieure 1 = VWAP + (1 × √Variance)
Bande Supérieure 2 = VWAP + (2 × √Variance)
```

### Money Flow Index (MFI)
```
Typical Price = (High + Low + Close) / 3
Raw Money Flow = Typical Price × Volume

Si TP_aujourd'hui > TP_hier:
    Positive Money Flow = Raw Money Flow
Sinon:
    Negative Money Flow = Raw Money Flow

Money Flow Ratio = Σ(Positive MF, 14) / Σ(Negative MF, 14)
MFI = 100 - (100 / (1 + Money Flow Ratio))
```

### Chaikin Money Flow (CMF)
```
Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low)
Money Flow Volume = MFM × Volume
CMF = Σ(Money Flow Volume, n) / Σ(Volume, n)
```

---

## 1.11 CCI (Commodity Channel Index)

### Formule complète (Donald Lambert, 1980)
```
Typical Price = (High + Low + Close) / 3
Mean Deviation = (1/n) × Σ|TP_i - SMA(TP, n)|
CCI = (TP - SMA(TP, n)) / (0.015 × Mean Deviation)
```

**Seuils** :

| Contexte | Suracheté | Survendu |
|----------|-----------|----------|
| Standard | +100 | -100 |
| Extrême | +200 | -200 |
| Crypto | +150 | -150 |

---

## 1.12 Williams %R

### Formule
```
%R = ((Highest High(n) - Close) / (Highest High(n) - Lowest Low(n))) × (-100)
```

**Relation avec Stochastique** :
```
%R = %K - 100
```

**Seuils** : Suracheté = -20, Survendu = -80

---

## 1.13 Fibonacci

### Niveaux de Retracement (dérivés de la suite de Fibonacci)
```
23.6% = tout nombre ÷ nombre 3 places à droite
38.2% = tout nombre ÷ nombre 2 places à droite
61.8% = tout nombre ÷ nombre suivant (ratio d'or)
78.6% = √0.618
```

**Formules de calcul** :
```
# Uptrend (mesure du pullback)
Niveau 23.6% = High - ((High - Low) × 0.236)
Niveau 38.2% = High - ((High - Low) × 0.382)
Niveau 50.0% = High - ((High - Low) × 0.500)
Niveau 61.8% = High - ((High - Low) × 0.618)
Niveau 78.6% = High - ((High - Low) × 0.786)
```

### Extensions Fibonacci
```
Point A = Début du mouvement initial
Point B = Fin du mouvement initial
Point C = Fin du retracement

Extension 127.2% = C + ((B - A) × 1.272)
Extension 161.8% = C + ((B - A) × 1.618)
Extension 200.0% = C + ((B - A) × 2.000)
Extension 261.8% = C + ((B - A) × 2.618)
```

---

## 1.14 Points Pivots

### Pivot Points Standard
```
PP = (High + Low + Close) / 3

R1 = (2 × PP) - Low
R2 = PP + (High - Low)
R3 = R2 + (High - Low)

S1 = (2 × PP) - High
S2 = PP - (High - Low)
S3 = S2 - (High - Low)
```

### Pivot Points Camarilla
```
Range = High - Low

R1 = Close + (Range × 1.1/12)
R2 = Close + (Range × 1.1/6)
R3 = Close + (Range × 1.1/4)
R4 = Close + (Range × 1.1/2)

S1 = Close - (Range × 1.1/12)
S2 = Close - (Range × 1.1/6)
S3 = Close - (Range × 1.1/4)
S4 = Close - (Range × 1.1/2)
```

### Pivot Points Fibonacci
```
PP = (High + Low + Close) / 3
Range = High - Low

R1 = PP + (Range × 0.382)
R2 = PP + (Range × 0.618)
R3 = PP + Range

S1 = PP - (Range × 0.382)
S2 = PP - (Range × 0.618)
S3 = PP - Range
```

---

# PARTIE 2 : PATTERNS ET FORMATIONS

## 2.1 Patterns de Chandeliers Japonais — Détection Algorithmique

### Patterns à 1 Chandelier

**Doji** :
```python
body_size = abs(Close - Open)
candle_range = High - Low
body_ratio = body_size / candle_range

is_doji = body_ratio <= 0.05  # Corps ≤ 5% de la range
```

**Hammer/Hanging Man** :
```python
is_hammer_shape = (
    body_size <= 0.33 × candle_range AND    # Petit corps
    lower_shadow >= 2 × body_size AND        # Ombre inférieure longue
    upper_shadow <= 0.10 × candle_range      # Peu ou pas d'ombre supérieure
)

is_hammer = is_hammer_shape AND in_downtrend
is_hanging_man = is_hammer_shape AND in_uptrend
```

**Marubozu** :
```python
is_bullish_marubozu = (
    Close > Open AND
    abs(Open - Low) <= 0.01 × (High - Low) AND
    abs(Close - High) <= 0.01 × (High - Low)
)
```

### Patterns à 2 Chandeliers

**Engulfing (Engloutissant)** :
```python
def is_bullish_engulfing(current, previous):
    return (
        previous['Close'] < previous['Open'] AND       # Précédent baissier
        current['Close'] > current['Open'] AND         # Actuel haussier
        current['Open'] < previous['Close'] AND        # Ouverture sous clôture précédente
        current['Close'] > previous['Open'] AND        # Clôture au-dessus ouverture précédente
        abs(current['Close'] - current['Open']) >      # Corps actuel plus grand
        abs(previous['Close'] - previous['Open'])
    )
```

**Piercing Line** :
```python
is_piercing_line = (
    previous_is_bearish AND
    current['Open'] < previous['Low'] AND          # Gap down
    current['Close'] > midpoint(previous) AND      # Clôture au-dessus du milieu
    current['Close'] < previous['Open'] AND        # Mais sous l'ouverture précédente
    current_is_bullish
)
```

### Patterns à 3 Chandeliers

**Morning Star** :
```python
def is_morning_star(c1, c2, c3):
    body1 = abs(c1['Close'] - c1['Open'])
    body2 = abs(c2['Close'] - c2['Open'])
    body3 = abs(c3['Close'] - c3['Open'])
    
    return (
        c1['Close'] < c1['Open'] AND          # Premier : grand baissier
        body2 < body1 × 0.3 AND               # Deuxième : petit corps (étoile)
        c2['High'] < c1['Close'] AND          # Gap down
        c3['Close'] > c3['Open'] AND          # Troisième : grand haussier
        c3['Close'] > midpoint(c1)            # Clôture au-dessus du milieu du premier
    )
```

**Three White Soldiers** :
```python
is_three_white_soldiers = (
    all_three_candles_bullish AND
    each_opens_within_previous_body AND
    each_closes_higher_than_previous AND
    all_upper_shadows < 0.10 × body AND
    all_bodies_similar_size  # ±20%
)
```

---

## 2.2 Patterns Chartistes — Détection Algorithmique

### Head and Shoulders (Tête et Épaules)

**Algorithme de détection** :
```python
def detect_head_and_shoulders(prices, window=5):
    # Trouver les extrema locaux
    local_max = argrelextrema(prices['high'].values, np.greater, order=window)
    local_min = argrelextrema(prices['low'].values, np.less, order=window)
    
    # Le pattern nécessite 5 points alternés
    for i in range(5, len(extrema)):
        e1, e2, e3, e4, e5 = extrema.iloc[i-5:i].values
        
        is_hs = (
            e1 > e2 AND                               # Épaule gauche > creux gauche
            e3 > e1 AND e3 > e5 AND                   # Tête > deux épaules
            abs(e1 - e5) <= 0.03 × mean([e1, e5]) AND # Épaules ~égales (3%)
            abs(e2 - e4) <= 0.03 × mean([e2, e4])     # Ligne de cou ~horizontale
        )
```

**Calcul de l'objectif de prix** :
```
neckline = ligne reliant e2 et e4
pattern_height = e3 - neckline_at_e3
target = breakout_point - pattern_height
```

### Double Top / Double Bottom

```python
def detect_double_top(prices, tolerance=0.02):
    peaks = find_local_maxima(prices, window=10)
    
    for i in range(1, len(peaks)):
        peak1, peak2 = peaks[i-1], peaks[i]
        
        if abs(peak1['price'] - peak2['price']) <= tolerance × peak1['price']:
            trough = find_min_between(prices, peak1['index'], peak2['index'])
            
            signal_line = trough['price']
            pattern_height = peak1['price'] - signal_line
            target = signal_line - pattern_height
            
            return {'signal_line': signal_line, 'target': target}
```

### Triangles

**Classification algorithmique** :
```python
def classify_triangle(upper_slope, lower_slope):
    if upper_slope ≈ 0 and lower_slope > 0:
        return "Triangle Ascendant"    # Résistance plate, support montant
    elif upper_slope < 0 and lower_slope ≈ 0:
        return "Triangle Descendant"   # Résistance descendante, support plat
    elif upper_slope < 0 and lower_slope > 0:
        return "Triangle Symétrique"   # Lignes convergentes
```

**Objectif de prix** :
```
triangle_height = max_high - min_low (point le plus large)
bullish_target = breakout_point + triangle_height
```

### ZigZag pour Détection de Pivots

```python
def zigzag(prices, deviation_threshold=5):
    pivots = []
    last_pivot = prices.iloc[0]
    current_direction = None
    
    for i, bar in prices.iterrows():
        if current_direction == 'up':
            if bar['high'] > last_pivot['price']:
                last_pivot = {'index': i, 'price': bar['high'], 'type': 'high'}
            elif (last_pivot['price'] - bar['low']) / last_pivot['price'] >= deviation_threshold / 100:
                pivots.append(last_pivot)
                last_pivot = {'index': i, 'price': bar['low'], 'type': 'low'}
                current_direction = 'down'
    
    return pivots
```

---

# PARTIE 3 : GESTION DU RISQUE ET MONEY MANAGEMENT

## 3.1 Position Sizing

### Kelly Criterion
```
f* = (p × b - q) / b
```
- **f*** : fraction optimale du capital à risquer
- **p** : probabilité de gain
- **q** : probabilité de perte (1 - p)
- **b** : ratio gain/perte moyen

**Formule alternative** :
```
Kelly % = W - [(1 - W) / R]
```
- **W** : taux de réussite
- **R** : ratio Risk/Reward

**Recommandations** :
- **Full Kelly** : croissance maximale mais drawdowns ~75%
- **Half-Kelly** (0.5 × f*) : ~75% de la croissance, drawdowns réduits
- **Quarter-Kelly** (0.25 × f*) : ~50% de la croissance, très stable
- **Crypto** : utiliser Quarter-Kelly maximum (0.1-0.25)

### Fixed Fractional
```
Position Size (unités) = (Équité × Risque %) / Risque par unité

Nombre d'actions = (Solde × Risque %) / (Prix d'entrée - Stop Loss)
```

**Pourcentages recommandés** :
- Conservateur : 0.5-1% par trade
- Modéré : 1-2% par trade
- Agressif : 2-3% par trade
- Maximum absolu : 5% par trade

### Volatility-Based Position Sizing
```
Position Size = (Équité × Volatilité Cible) / (ATR × Multiplicateur × √252)
```

---

## 3.2 Méthodes de Stop-Loss

### ATR-Based Stops
```
Stop Loss (Long) = Prix d'entrée - (ATR × Multiplicateur)
Stop Loss (Short) = Prix d'entrée + (ATR × Multiplicateur)
```

**Multiplicateurs recommandés** :

| Marché | Multiplicateur |
|--------|----------------|
| Stocks (faible vol) | 1.5-2.0× |
| Stocks (normal) | 2.0-2.5× |
| Crypto | 3.0-4.0× |

### Chandelier Exit
```
Long : Chandelier = Plus Haut (n périodes) - (ATR × 3.0)
Short : Chandelier = Plus Bas (n périodes) + (ATR × 3.0)
```

### Trailing Stop
```python
class ATRTrailingStop:
    def update(self, current_price, atr, direction):
        if direction == "LONG":
            if current_price > self.highest_price:
                self.highest_price = current_price
            stop_level = self.highest_price - (atr * self.multiplier)
        return stop_level
```

---

## 3.3 Métriques de Performance

### Sharpe Ratio
```
Sharpe = (Rp - Rf) / σp
```
- **Rp** : rendement du portefeuille (annualisé)
- **Rf** : taux sans risque
- **σp** : écart-type du portefeuille

**Annualisation** :
```
Sharpe Annualisé = Sharpe Journalier × √252
```

**Benchmarks** : < 1.0 suboptimal, 1.0-2.0 bon, > 2.0 excellent

### Sortino Ratio
```
Sortino = (Rp - Rf) / σd
σd = √[Σ(min(0, Ri - MAR)²) / n]
```
Ne considère que les rendements négatifs (downside deviation).

### Calmar Ratio
```
Calmar = CAGR / |Maximum Drawdown|
```
**Benchmarks** : < 1.0 pauvre, 1.0-3.0 bon, > 3.0 excellent

### Maximum Drawdown
```
MDD = max[(Peak_t - Trough_t) / Peak_t]
```

### Profit Factor
```
Profit Factor = Σ(Trades gagnants) / |Σ(Trades perdants)|
```
**Benchmarks** : < 1.5 marginal, 1.5-2.0 bon, > 2.0 excellent

### Expectancy
```
Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
```

---

## 3.4 Value at Risk (VaR)

### VaR Paramétrique
```
VaR = -[μ - (z × σ)] × Valeur du Portefeuille
```

**Z-scores** :
- 95% confiance : z = 1.645
- 99% confiance : z = 2.326

### VaR Historique
```
1. Collecter les rendements historiques (ex: 250 jours)
2. Trier du pire au meilleur
3. VaR = |Rendement au percentile| × Valeur du Portefeuille

Pour 95% VaR avec 250 observations :
VaR = 13ème pire rendement journalier × Portefeuille
```

### CVaR (Expected Shortfall)
```
CVaR = Moyenne de toutes les pertes dépassant le seuil VaR
```

---

# PARTIE 4 : STRATÉGIES DE TRADING QUANTITATIVES

## 4.1 Mean Reversion

### Processus Ornstein-Uhlenbeck
```
dXt = μ(θ - Xt)dt + σdBt
```
- **θ** : niveau moyen de long terme
- **μ** : vitesse de réversion
- **σ** : volatilité instantanée

### Half-Life de Mean Reversion
```
t₀.₅ = ln(2) / θ = -ln(2) / λ
```
Où λ est le coefficient de régression ADF.

### Z-Score pour Signaux
```
Z(t) = (Price(t) - μt) / σt
μt = Moyenne mobile sur période lookback
σt = Écart-type mobile
```

**Règles d'entrée/sortie** :

| Signal | Condition | Action |
|--------|-----------|--------|
| Entrée Long | Z-score < -2.0 | Acheter |
| Entrée Short | Z-score > +2.0 | Vendre |
| Sortie Long | Z-score croise 0 | Fermer long |
| Sortie Short | Z-score croise 0 | Fermer short |
| Stop-Loss | |Z-score| > 3.0 | Sortie immédiate |

---

## 4.2 Momentum Strategies

### Time-Series Momentum (TSMOM)
```
Signal(t) = sign(r(t-12, t-1))
Position = Signal × (Volatilité Cible / Volatilité Réalisée)
```

### Cross-Sectional Momentum
```
1. Classer tous les titres par rendements sur 12 mois (excluant dernier mois)
2. Long sur le décile supérieur (gagnants)
3. Short sur le décile inférieur (perdants)
4. Détenir 1-12 mois
```

### Dual Momentum
```python
if Asset_Return(12m) > Benchmark_Return(12m) AND Asset_Return(12m) > 0:
    Position = Long Asset
else:
    Position = Cash ou Obligations
```

---

## 4.3 Breakout Strategies

### Donchian Channel Breakout
```
Upper Band = Plus Haut sur N périodes
Lower Band = Plus Bas sur N périodes

Long Entry : Close > Upper Band
Short Entry : Close < Lower Band
```

**Paramètres** :

| Style | Entrée | Sortie |
|-------|--------|--------|
| Day Trading | 10-20 | 5-10 |
| Swing Trading | 20-55 | 10-20 |
| Position | 55-100 | 20-55 |

### Volatility Breakout (ATR-Based)
```
Long Entry : Close > (Open + k × ATR)
Short Entry : Close < (Open - k × ATR)
k = 1.0 à 2.0
```

---

## 4.4 Trend Following — Turtle Trading

### Règles d'entrée
```
Système 1 (20 jours) : Entrée si Price > Plus Haut 20 jours
Système 2 (55 jours) : Entrée si Price > Plus Haut 55 jours
```

### Position Sizing
```
N = EMA 20 jours du True Range
Dollar Volatility = N × Dollars par point
Unit Size = (1% du Compte) / Dollar Volatility
```

### Limites de position
- Marché unique : 4 unités max
- Marchés corrélés : 6 unités max
- Direction unique : 12 unités max

### Stops et Sorties
```
Stop Initial = Prix d'entrée - (2N)
Pyramiding : Ajouter 1 unité tous les 0.5N favorables
Sortie Système 1 : Plus Bas 10 jours
Sortie Système 2 : Plus Bas 20 jours
```

---

## 4.5 Statistical Arbitrage / Pairs Trading

### Sélection de paires
1. Même secteur/industrie
2. Corrélation > 0.7
3. Test de cointégration ADF : p-value < 0.05
4. Half-life raisonnable : 5-30 jours

### Calcul du Spread
```
Spread = ln(Price_A) - β × ln(Price_B)
```

### Hedge Ratio (régression OLS)
```
Price_A = α + β × Price_B + ε
Hedge Ratio = β
```

### Signaux d'entrée/sortie
```
Entrée Long Spread : Z-score < -2.0
Entrée Short Spread : Z-score > +2.0
Sortie : Z-score croise 0
Stop-Loss : |Z-score| > 3.0 ou perte de cointégration
```

---

# PARTIE 5 : BACKTESTING ET VALIDATION

## 5.1 Walk-Forward Optimization

### Méthodologie
```
1. Diviser données en périodes séquentielles
2. Optimiser sur in-sample (70%)
3. Tester sur out-of-sample (30%)
4. Enregistrer performance OOS
5. Avancer et répéter
6. Concaténer tous les résultats OOS
```

### Purged Cross-Validation (López de Prado)
```
| Training Set | Purge Zone | Test Set | Embargo Zone | Training Set |
```
- **Purging** : retirer du training toute observation dans la période de formation du label test
- **Embargo** : exclure 1-5% des données après chaque test fold

---

## 5.2 Prévention de l'Overfitting

### Deflated Sharpe Ratio
```
DSR = Φ[(SR* - SR₀) / σ_SR₀]

σ_SR₀ = √[(1 - γ₃·SR₀ + ((γ₄-1)/4)·SR₀²) / (T-1)]
```
- **γ₃** : skewness des rendements
- **γ₄** : kurtosis des rendements

### Règles pratiques
- Minimum 252 observations par paramètre
- Éviter les "îlots de paramètres" (zones optimales étroites)
- Préférer les plateaux robustes aux pics aigus
- Red flags : Sharpe > 3 sans explication, équity curve trop lisse

---

## 5.3 Métriques de Performance

| Métrique | Formule |
|----------|---------|
| Total Return | (V_final - V_initial) / V_initial |
| CAGR | (V_final / V_initial)^(365/jours) - 1 |
| Volatilité | σ_daily × √252 |
| Win Rate | Trades gagnants / Total trades |
| Payoff Ratio | Avg Win / Avg Loss |
| Exposure | Temps en position / Temps total |

---

# PARTIE 6 : MICROSTRUCTURE DES MARCHÉS

## 6.1 Order Book

### Bid-Ask Spread
```
Spread Absolu = Best Ask - Best Bid
Spread Relatif = (Best Ask - Best Bid) / Mid Price × 100%
```

### Mid-Price
```
Mid Price = (Best Bid + Best Ask) / 2
```

### Weighted Mid-Price
```
Weighted Mid = (Bid × Ask_Volume + Ask × Bid_Volume) / (Bid_Volume + Ask_Volume)
```

### Order Book Imbalance
```
Imbalance = (Bid Volume - Ask Volume) / (Bid Volume + Ask Volume)
Range : [-1, 1]
Positif = pression acheteuse, Négatif = pression vendeuse
```

---

## 6.2 Slippage

### Modèle Square-Root (Kyle/Obizhaeva)
```
Market Impact = σ × √(Q / V)
```
- **σ** : volatilité journalière
- **Q** : taille du trade
- **V** : volume journalier moyen

**Exemple** : σ = 2%, V = 1M actions, Q = 50K actions (5% ADV)
```
Impact = 0.02 × √(0.05) ≈ 0.45% ou 45 bps
```

### Coût Total d'Exécution
```
Total Cost = Commission + Spread + Market Impact + Opportunity Cost
Implementation Shortfall = (Prix Exécution - Prix Décision) / Prix Décision
```

---

# PARTIE 7 : SPÉCIFICITÉS CRYPTO VS ACTIONS

## 7.1 Différences de Volatilité

| Actif | Volatilité Annualisée |
|-------|----------------------|
| Bitcoin | ~75% (5-7x S&P 500) |
| S&P 500 | ~15-20% |
| Altcoins | 2-3x Bitcoin |

**Ajustements recommandés** :
```
CRYPTO:
  bollinger_std_dev: 2.5-3.0
  atr_multiplier: 2.5-4.0
  stop_loss_multiplier: 3.0-4.0

STOCKS:
  bollinger_std_dev: 2.0
  atr_multiplier: 1.5-2.0
  stop_loss_multiplier: 2.0
```

## 7.2 Trading 24/7

- Pas de gaps overnight en crypto
- Liquidité plus faible le weekend (spreads 2-3x plus larges)
- Sessions à considérer (UTC) : Asie (00:00-08:00), Europe (08:00-16:00), US (14:00-22:00)

## 7.3 Funding Rates (Perpetuals)
```python
funding_cost = position_size × funding_rate × (holding_hours / 8)
# Typique : 0.01% par 8h (neutre), 0.1%+ (sentiment fort)
```

---

# PARTIE 8 : SIGNAUX D'ENTRÉE ET DE SORTIE

## 8.1 Conditions Algorithmiques d'Entrée

### Triple Confirmation
```python
LONG_ENTRY = (
    (close > ema_200) AND                    # Filtre tendance
    (rsi > 30 AND rsi < 70) AND              # RSI en zone neutre
    (macd_line > signal_line) AND            # MACD haussier
    (adx > 25) AND                           # Tendance établie
    (volume > avg_volume * 1.2)              # Confirmation volume
)
```

### Multi-Timeframe Analysis
```python
def mtf_entry(htf_trend, ltf_signal, ltf_rsi):
    valid_long = htf_trend == "BULL" AND ltf_signal == "LONG"
    valid_short = htf_trend == "BEAR" AND ltf_signal == "SHORT"
    
    rsi_confirms_long = ltf_rsi < 65
    rsi_confirms_short = ltf_rsi > 35
    
    return {
        "long": valid_long AND rsi_confirms_long,
        "short": valid_short AND rsi_confirms_short
    }
```

## 8.2 Filtres

### ADX Trend Filter
```python
def adx_filter(adx, threshold=25):
    trending = adx > threshold
    # ADX > 25 : utiliser trend-following
    # ADX < 20 : utiliser mean-reversion
    return trending
```

### Volume Filter
```python
def volume_filter(volume, avg_volume, min_multiplier=1.0):
    return volume >= avg_volume * min_multiplier
```

## 8.3 Signal Strength Scoring

```python
def calculate_signal_strength(signals):
    score = 0
    
    if signals['trend_aligned']: score += 25
    if signals['rsi_confirms']: score += 15
    if signals['macd_confirms']: score += 10
    if signals['volume_above_avg']: score += 20
    if signals['htf_aligned']: score += 20
    
    adx = signals.get('adx', 0)
    if adx > 20: score += min(10, (adx - 20) / 3)
    
    return min(score, 100)
```

## 8.4 Machine d'États pour Gestion de Position

```python
class TradingStateMachine:
    STATES = ["SCANNING", "ARMED", "IN_POSITION", "COOLDOWN"]
    
    def transition(self, signal, filters_pass):
        if self.state == "SCANNING":
            if signal AND filters_pass:
                self.state = "ARMED"
                
        elif self.state == "ARMED":
            if self.confirm_entry():
                self.state = "IN_POSITION"
                self.execute_entry()
            elif self.signal_invalidated():
                self.state = "SCANNING"
                
        elif self.state == "IN_POSITION":
            if self.check_exit():
                self.execute_exit()
                self.state = "COOLDOWN"
                self.cooldown_bars = 5
                
        elif self.state == "COOLDOWN":
            self.cooldown_bars -= 1
            if self.cooldown_bars <= 0:
                self.state = "SCANNING"
```

---

# ANNEXE : PARAMÈTRES RECOMMANDÉS PAR CONTEXTE

## Day Trading

| Indicateur | Stocks | Crypto |
|------------|--------|--------|
| RSI période | 7-9 | 7-10 |
| EMA rapide/lente | 8/21 | 7/21 |
| MACD | 5/13/1 | 8/21/5 |
| Bollinger | 10, 1.5σ | 10, 2.0σ |
| ATR période | 14 | 10-14 |
| Stop multiplier | 1.5-2.0 ATR | 2.5-3.5 ATR |
| Risk par trade | 1-2% | 0.5-1% |

## Swing Trading

| Indicateur | Stocks | Crypto |
|------------|--------|--------|
| RSI période | 14-21 | 14 |
| EMA rapide/lente | 12/26 | 10/21 |
| MACD | 12/26/9 | 12/26/9 |
| Bollinger | 20, 2.0σ | 20, 2.5σ |
| ATR période | 14-21 | 14-20 |
| Stop multiplier | 2.0-2.5 ATR | 3.0-4.0 ATR |
| Risk par trade | 1-2% | 0.5-1.5% |

---

Cette documentation fournit toutes les formules mathématiques et conditions algorithmiques nécessaires pour implémenter un système de trading complet. Chaque indicateur inclut ses paramètres optimaux pour différents contextes (day trading vs swing trading, stocks vs crypto), permettant une adaptation précise aux conditions de marché visées.