# Guide complet du trading crypto algorithmique

Le trading algorithmique de cryptomonnaies repose sur trois piliers fondamentaux : l'analyse technique pour identifier les opportunités, la gestion du risque pour préserver le capital, et l'analyse on-chain pour comprendre les mouvements institutionnels. Ce guide fournit les paramètres exacts, formules et règles programmables pour construire un bot de trading rentable.

## L'analyse technique : les fondations programmables

L'efficacité d'un bot de trading dépend de règles d'entrée et de sortie précises basées sur des indicateurs mathématiques. Les paramètres suivants représentent le consensus des traders professionnels pour les marchés crypto.

### Configuration optimale des indicateurs

Le **RSI (Relative Strength Index)** utilise une période de **14** par défaut, avec des seuils de **30/70** en conditions normales. Pour le crypto, les seuils **20/80** capturent mieux les extrêmes de volatilité. La formule est : `RSI = 100 - (100 / (1 + RS))` où RS = Moyenne des gains / Moyenne des pertes sur n périodes.

Le **MACD** conserve ses paramètres classiques : EMA rapide **12**, EMA lente **26**, ligne de signal **9**. Un signal d'achat se déclenche quand la ligne MACD croise au-dessus de la ligne de signal, particulièrement sous la ligne zéro.

Les **Bollinger Bands** utilisent une période de **20-21** avec **2.0 écarts-types**. La détection de squeeze (compression de volatilité) s'effectue quand : `BBW < SMA(BBW, 50) × 0.75`, signalant un breakout imminent.

Les **moyennes mobiles** recommandées sont :
- **9 EMA** : momentum court terme et scalping
- **21 EMA** : tendance court terme, day trading
- **50 SMA/EMA** : tendance moyen terme
- **200 SMA** : tendance long terme et support/résistance majeur

L'**ATR (Average True Range)** sur **14 périodes** sert principalement au placement des stop-loss. La formule standard pour un stop : `Stop = Entry ± (ATR × 2.0)` avec un multiplicateur de **2.5-3.0** pour les cryptos volatiles.

### Patterns de chandeliers japonais avec critères de validation

**Hammer (fiabilité 8/10)** : mèche inférieure ≥ 2× corps, mèche supérieure ≤ 10% du range, doit apparaître en bas de tendance baissière. Formule : `(open - low) >= 2 × |open - close| AND (high - max(open,close)) <= 0.1 × (high - low)`.

**Engulfing (fiabilité 9/10)** : le corps de la bougie actuelle englobe entièrement le corps précédent. Bullish engulfing : `current_close > prev_open AND current_open < prev_close`.

**Morning/Evening Star (fiabilité 9/10)** : pattern à 3 bougies où la bougie centrale est un petit corps, et la troisième bougie clôture au-delà du point médian de la première.

### Niveaux Fibonacci et divergences

Les retracements clés sont **38.2%**, **50%**, **61.8%** (ratio doré) et **78.6%**. Pour les extensions (take-profit), utiliser **127.2%**, **161.8%** et **200%**.

Les **divergences RSI/MACD** constituent des signaux puissants de retournement :
- **Divergence régulière baissière** : prix fait des higher highs, indicateur fait des lower highs → retournement probable
- **Divergence cachée haussière** : prix fait des higher lows, indicateur fait des lower lows → continuation de tendance

---

## L'analyse on-chain : lire les mouvements institutionnels

L'analyse on-chain offre un avantage unique en crypto en révélant le comportement des holders et des institutions directement sur la blockchain.

### Métriques essentielles et seuils de trading

Le **MVRV Ratio** (Market Value to Realized Value) mesure le profit non réalisé de l'ensemble du marché :

| MVRV | Signal | Action |
|------|--------|--------|
| **> 3.5** | Euphorie extrême | **VENDRE** - distribution probable |
| **> 2.4** | Marché surchauffé | Prendre des profits partiels |
| **= 1.0** | Point d'équilibre | Neutre |
| **< 1.0** | Marché sous l'eau | **ACHETER** - zone d'accumulation |
| **< 0.8** | Sous-évaluation extrême | **ACHAT FORT** - capitulation |

Le **NUPL** (Net Unrealized Profit/Loss) identifie les phases du cycle :
- **> 0.75** : Euphorie (zone bleue) → **VENDRE**
- **0.50-0.75** : Conviction forte → Réduire l'exposition
- **0.25-0.50** : Optimisme → Conserver
- **< 0** : Capitulation (zone rouge) → **ACHETER**

Les tops historiques Bitcoin ont atteint des NUPL de 0.793 (2017) et 0.748 (2021).

Le **SOPR** (Spent Output Profit Ratio) mesure le profit/perte des coins dépensés en temps réel. En tendance haussière, un **reset du SOPR à 1.0** constitue un excellent signal d'achat ("buy the dip").

### Flux d'exchange et mouvements de whales

| Type de flux | Signification | Signal |
|--------------|---------------|--------|
| **Inflows élevés** | Coins vers exchanges | Pression vendeuse → **BEARISH** |
| **Outflows élevés** | Coins hors exchanges | Accumulation → **BULLISH** |

Seuils pour les transactions "whale" : **> 100 BTC** ou **> 1000 ETH** ou **> $500K-$1M USD**.

### Données derivatives

Les **funding rates** révèlent le biais du marché :
- **> 0.1% (8h)** : Longs extrêmement surchargés → correction probable, biais SHORT
- **> 0.05%** : Prudence sur nouveaux longs
- **< 0%** : Shorts dominants → setup potentiel de long squeeze

L'**Open Interest** combiné au prix :
- OI croissant + Prix croissant = Nouvelle argent entrant long → continuation
- OI croissant + Prix décroissant = Nouveaux shorts → pression baissière
- OI décroissant + Prix croissant = Short covering → épuisement potentiel

### APIs pour intégration bot

**Glassnode** (REST) : `https://api.glassnode.com/v1/metrics/` - MVRV, NUPL, SOPR, exchange flows
**CoinGlass** : Liquidations, funding rates, OI en temps réel
**Santiment** (GraphQL) : Métriques sociales et on-chain
**Nansen** : Tracking smart money avec 500M+ wallets labellisés

---

## La gestion du risque : protéger son capital

La gestion du risque différencie les traders rentables des perdants. Ces règles doivent être codées en dur dans tout bot de trading.

### Position sizing

La **méthode du pourcentage fixe** est la plus fiable :
- **Conservateur** : 0.5-1% du capital par trade
- **Standard** : 1-2% (recommandé)
- **Maximum absolu** : 3%

**Formule** : `Position Size = (Capital × Risk%) / Stop Loss Distance`

Le **Kelly Criterion** optimise mathématiquement la taille : `Kelly% = W - [(1-W) / R]` où W = Win Rate et R = Risk/Reward ratio. **CRUCIAL** : utiliser le **Quarter-Kelly (25%)** pour réduire la volatilité tout en capturant ~50% de la croissance optimale.

Le **position sizing basé sur l'ATR** ajuste automatiquement selon la volatilité :
`Position Size = (Capital × Risk%) / (ATR × Multiplier)`

### Stop-loss et take-profit

**Multiplicateurs ATR par style** :

| Style | ATR Multiplier |
|-------|----------------|
| Day trading | 1.5-2.0× |
| Swing trading | 2.0-2.5× |
| Position trading | 2.5-3.0× |
| Haute volatilité | 3.0-4.0× |

**Trailing stop progressif** :
```
À 1R de profit : Stop au breakeven
À 2R de profit : Stop verrouille 1R
À 3R de profit : Stop verrouille 2R
Puis trailing à 1× ATR du prix
```

**Scaling out** recommandé :
- 33% à 1R, déplacer stop au breakeven
- 33% à 2R, trailing sur le reste
- 34% final avec trailing stop

### Limites de drawdown

| Type | Limite | Action |
|------|--------|--------|
| **Daily loss** | 2-3% | Stop trading pour la journée |
| **Weekly loss** | 4-6% | Réduire position size de 50% |
| **Max drawdown** | 15-20% | Pause totale et révision stratégie |
| **Losses consécutives** | 3 | Pause 15 minutes minimum |

**Table de récupération** importante :
- 10% drawdown → nécessite 11.1% pour récupérer
- 20% drawdown → nécessite 25%
- 50% drawdown → nécessite **100%**

---

## Stratégies quantitatives programmables

### Mean reversion avec Bollinger Bands

```python
# Paramètres
BB_PERIOD = 20
BB_STD = 2.0
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# Règles d'entrée
LONG: price < lower_band AND RSI < 30
SHORT: price > upper_band AND RSI > 70

# Sortie
TARGET: middle_band (SMA 20)
STOP: 1.5× ATR au-delà de l'entrée
```

### EMA Crossover avec confirmation

```python
# Paramètres
FAST_EMA = 9
SLOW_EMA = 21
ADX_THRESHOLD = 25

# Règles
LONG: EMA_9 crosses above EMA_21 AND ADX > 25 AND RSI > 50
SHORT: EMA_9 crosses below EMA_21 AND ADX > 25 AND RSI < 50

# Gestion
STOP: 2× ATR
TARGET: 1:2 risk-reward minimum
```

### Breakout avec filtre de volume

```python
# Identification des niveaux
resistance = rolling_max(high, 20)
support = rolling_min(low, 20)
avg_volume = SMA(volume, 20)

# Entrée breakout
LONG: close > resistance AND volume > avg_volume × 1.5
SHORT: close < support AND volume > avg_volume × 1.5

# Filtre anti-fakeout
CONFIRM: ADX rising toward 25-40 zone
STOP: 1.5× ATR
TARGET: range_height projeté depuis breakout
```

### Grid trading pour marchés ranging

```python
CONFIG = {
    'lower_price': 60000,
    'upper_price': 70000,
    'num_grids': 20,
    'grid_spacing': 0.5%,  # Par niveau
    'total_investment': 10000
}

# Calcul géométrique (recommandé pour crypto)
ratio = (upper / lower) ** (1 / num_grids)
levels = [lower × ratio^i for i in range(num_grids + 1)]

# Règles
- Placer buy orders sous le prix actuel à chaque niveau
- Placer sell orders au-dessus
- Quand buy remplit → placer sell au niveau supérieur
- Stop-loss global sous le niveau le plus bas
```

### DCA intelligent avec triggers techniques

```python
BASE_ORDER = 100  # USDT
SAFETY_ORDERS = 5
SCALE = 1.5  # Multiplicateur de taille

# Triggers RSI pour safety orders
RSI_LEVELS = [29, 27.5, 26, 24, 22]
PRICE_DROPS = [1.5%, 2.5%, 4%, 6%, 10%]

# Logic
IF rsi < RSI_LEVELS[n] AND price_drop > PRICE_DROPS[n]:
    PLACE safety_order[n] with size = BASE × SCALE^n
```

---

## Market microstructure et détection de manipulation

### Order book imbalance

```python
# Calcul du déséquilibre
OBI = (Σ bid_qty - Σ ask_qty) / (Σ bid_qty + Σ ask_qty)

# Signaux
OBI > 0.3: Pression acheteuse → BULLISH
OBI < -0.3: Pression vendeuse → BEARISH
```

### Volume Profile

Le **POC (Point of Control)** représente le prix avec le plus grand volume échangé - agit comme aimant/support/résistance. La **Value Area** contient 70% du volume et définit les zones de valeur.

### Détection du spoofing

```python
def detect_spoofing():
    for order in large_orders:
        if order.cancelled_within(seconds=1):
            if order.price_was_approached:
                flag_spoofing()
    
    # Seuil: >80% taux d'annulation sur gros ordres
    if cancel_rate > 0.8:
        high_spoof_probability = True
```

### Protection anti-manipulation

| Métrique | Safe | Caution | Éviter |
|----------|------|---------|--------|
| Spread % | <0.05% | 0.05-0.2% | >0.2% |
| Vol/Depth ratio | <10 | 10-30 | >50 |
| Cancel rate | <30% | 30-60% | >80% |

---

## ICT et Smart Money Concepts pour le bot

Les concepts ICT (Inner Circle Trader) identifient les "empreintes" institutionnelles dans le prix.

### Order Blocks programmables

**Bullish OB** : dernière bougie baissière avant un mouvement haussier fort avec displacement.
**Bearish OB** : dernière bougie haussière avant un mouvement baissier fort.

```python
# Identification
displacement = abs(close - open) > ATR × 2
bullish_ob = bearish_candle BEFORE displacement_up
bearish_ob = bullish_candle BEFORE displacement_down

# Entrée
LONG: price retrace to bullish_ob zone AND shows rejection
STOP: below order_block
TARGET: next liquidity pool
```

### Fair Value Gaps (FVG)

Pattern à 3 bougies où le corps/mèche de la bougie centrale ne touche pas les mèches des bougies environnantes.

```python
# Bullish FVG
bullish_fvg = candle1.high < candle3.low

# Trading
ENTRY: price retrace to FVG midpoint (Consequent Encroachment)
```

### Structure de marché

**BOS (Break of Structure)** : cassure du swing précédent dans la direction de la tendance → continuation
**CHoCH (Change of Character)** : première cassure contre la tendance actuelle → retournement potentiel

```python
# Détection
uptrend = higher_highs AND higher_lows
BOS_bullish = close > previous_swing_high (body close required)
CHoCH_bearish = close < swing_that_produced_last_BOS
```

### Kill Zones (fenêtres optimales)

- **London** : 2:00-5:00 AM EST
- **New York** : 7:00-10:00 AM EST
- **Silver Bullet** : 10:00-11:00 AM EST

---

## Backtesting et optimisation

### Walk-forward analysis

1. Diviser les données en segments séquentiels
2. **In-sample (70%)** : optimiser les paramètres
3. **Out-of-sample (30%)** : tester les paramètres optimisés
4. Avancer la fenêtre, répéter
5. Combiner tous les résultats out-of-sample

Minimum **6-12 périodes** de walk-forward pour validation robuste.

### Éviter l'overfitting

- Limiter le nombre de paramètres
- Choisir des paramètres dans des "régions favorables" (plateau performance)
- Tester la sensibilité ±10-20% sur chaque paramètre
- Si les résultats changent drastiquement → stratégie fragile

### Coûts à inclure

```python
# Calcul profit net
net_profit = gross_profit - (commission × 2) - slippage - spread

# Slippage estimé
liquid_majors: 0.01-0.03%
haute_volatilité: 0.05-0.1%
altcoins: 0.5-1%
```

**Seuil minimum de profit** avec fees de 0.1% : mouvement de **0.5%+** nécessaire pour être rentable.

---

## Ressources éducatives recommandées

### Livres essentiels

- **"Trading in the Zone"** de Mark Douglas - Psychologie fondamentale
- **"Technical Analysis of the Financial Markets"** de John Murphy - Bible de l'AT
- **"Quantitative Trading"** d'Ernest Chan - Introduction au trading quantitatif
- **"Machine Learning for Algorithmic Trading"** de Stefan Jansen - ML appliqué
- **"Market Wizards"** de Jack Schwager - Interviews de traders légendaires

### Chaînes YouTube de qualité

- **Coin Bureau** - Analyse crypto approfondie et research-backed
- **Benjamin Cowen** - Approche quantitative sans hype
- **Michael J. Huddleston (ICT)** - Concepts ICT originaux

### Méthodologies à maîtriser

**Wyckoff** : Phases d'accumulation/distribution, Spring (buy signal), UTAD (sell signal)
**Elliott Wave** : Structure 5-3 waves, relations Fibonacci entre waves
**Auction Market Theory** : POC, Value Area, balance/imbalance

---

## Checklist d'implémentation finale

### Paramètres core du bot

```python
# Position Sizing
MAX_RISK_PER_TRADE = 0.01  # 1%
MAX_RISK_PER_DAY = 0.03    # 3%
MAX_RISK_TOTAL = 0.06      # 6%

# Indicateurs
RSI_PERIOD = 14
RSI_OVERSOLD, RSI_OVERBOUGHT = 30, 70
EMA_FAST, EMA_SLOW = 9, 21
BB_PERIOD, BB_STD = 20, 2.0
ATR_PERIOD = 14
ATR_STOP_MULTIPLIER = 2.0

# Risk Management
MIN_RR_RATIO = 2.0
MAX_DAILY_DRAWDOWN = 0.03
MAX_TOTAL_DRAWDOWN = 0.15
CONSECUTIVE_LOSS_PAUSE = 3

# Fees
MIN_PROFIT_THRESHOLD = 0.005  # 0.5%
```

### Logique d'entrée universelle

```python
def check_entry():
    # 1. Filtre de tendance HTF
    trend = price > EMA_200
    
    # 2. Signal technique
    rsi_signal = RSI < 30 or RSI_cross_above(30)
    macd_signal = MACD > Signal AND Histogram > 0
    
    # 3. Confirmation volume
    volume_confirm = volume > SMA_volume × 1.5
    
    # 4. Price action
    pattern = bullish_engulfing() or hammer()
    
    # 5. Market regime
    regime = ADX > 25  # Trending
    
    return trend AND (rsi_signal OR macd_signal) AND volume_confirm AND pattern
```

### Vérifications pré-trade

```python
def pre_trade_checks():
    assert daily_loss < MAX_DAILY_DRAWDOWN
    assert consecutive_losses < 3
    assert total_exposure < 6%
    assert spread < 0.2%
    assert sufficient_liquidity
    return True
```

Ce guide fournit les fondations complètes pour construire un bot de trading crypto profitable. La clé du succès réside dans l'application rigoureuse de la gestion du risque, le backtesting exhaustif avant déploiement live, et l'adaptation continue aux conditions de marché changeantes.