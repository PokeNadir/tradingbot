import { useState, useEffect, useMemo } from 'react'
import PriceChart from './PriceChart'
import TradeProposal from './TradeProposal'
import IndicatorGauge from './IndicatorGauge'
import Portfolio from './Portfolio'
import TradeHistory from './TradeHistory'
import OnChainMetrics from './OnChainMetrics'
import MarketStructure from './MarketStructure'
import { formatCurrency, formatPercent } from '../utils/calculations'

// All available symbols grouped by category
const SYMBOL_GROUPS = {
  'Majors': ['BTC/USDT', 'ETH/USDT'],
  'Layer 1': ['SOL/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT', 'ATOM/USDT', 'NEAR/USDT', 'FTM/USDT'],
  'Layer 2 / DeFi': ['ARB/USDT', 'OP/USDT', 'LINK/USDT', 'UNI/USDT', 'AAVE/USDT'],
  'Meme': ['DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT'],
  'Others': ['XRP/USDT', 'LTC/USDT']
}

const ALL_SYMBOLS = Object.values(SYMBOL_GROUPS).flat()

const TIMEFRAMES = [
  { value: '1m', label: '1m' },
  { value: '5m', label: '5m' },
  { value: '15m', label: '15m' },
  { value: '30m', label: '30m' },
  { value: '1h', label: '1H' },
  { value: '4h', label: '4H' },
  { value: '1d', label: '1D' },
]

export default function Dashboard({
  portfolio = null,
  positions = [],
  signals = [],
  tickers = {},
  connected = false,
  onExecuteTrade,
  onClosePosition
}) {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT')
  const [selectedTimeframe, setSelectedTimeframe] = useState('15m')
  const [ohlcvData, setOhlcvData] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [trades, setTrades] = useState([])
  const [riskData, setRiskData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [showSymbolDropdown, setShowSymbolDropdown] = useState(false)

  // Filter symbols based on search query
  const filteredSymbols = useMemo(() => {
    if (!searchQuery) return ALL_SYMBOLS
    const query = searchQuery.toUpperCase()
    return ALL_SYMBOLS.filter(s => s.includes(query))
  }, [searchQuery])

  // Fetch OHLCV data when symbol or timeframe changes
  useEffect(() => {
    fetchOHLCV()
    fetchAnalysis()
  }, [selectedSymbol, selectedTimeframe])

  // Fetch trade history on mount
  useEffect(() => {
    fetchTrades()
    fetchRisk()
  }, [])

  async function fetchOHLCV() {
    setLoading(true)
    try {
      const [base, quote] = selectedSymbol.split('/')
      const response = await fetch(`/api/ohlcv/${base}/${quote}?timeframe=${selectedTimeframe}&limit=300`)
      if (response.ok) {
        const data = await response.json()
        setOhlcvData(data.ohlcv || [])
      }
    } catch (error) {
      console.error('Error fetching OHLCV:', error)
    } finally {
      setLoading(false)
    }
  }

  async function fetchAnalysis() {
    try {
      const [base, quote] = selectedSymbol.split('/')
      const response = await fetch(`/api/analysis/${base}/${quote}`)
      if (response.ok) {
        const data = await response.json()
        setAnalysis(data)
      }
    } catch (error) {
      console.error('Error fetching analysis:', error)
    }
  }

  async function fetchTrades() {
    try {
      const response = await fetch('/api/trades?limit=20')
      if (response.ok) {
        const data = await response.json()
        setTrades(data.trades || [])
      }
    } catch (error) {
      console.error('Error fetching trades:', error)
    }
  }

  async function fetchRisk() {
    try {
      const response = await fetch('/api/risk')
      if (response.ok) {
        const data = await response.json()
        setRiskData(data)
      }
    } catch (error) {
      console.error('Error fetching risk:', error)
    }
  }

  const currentTicker = tickers[selectedSymbol] || {}
  const currentSignals = signals.filter(s => s.symbol === selectedSymbol)

  return (
    <div className="min-h-screen bg-dark-bg text-white">
      {/* Header */}
      <header className="bg-dark-card border-b border-dark-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-accent-blue">Trading Bot</h1>
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              connected ? 'bg-accent-green/20 text-accent-green' : 'bg-accent-red/20 text-accent-red'
            }`}>
              <span className={`w-2 h-2 rounded-full ${connected ? 'bg-accent-green' : 'bg-accent-red'}`}></span>
              {connected ? 'Connected' : 'Disconnected'}
            </div>
          </div>

          {/* Symbol Selector with Search */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <button
                onClick={() => setShowSymbolDropdown(!showSymbolDropdown)}
                className="flex items-center gap-2 px-4 py-2 bg-dark-surface rounded-lg hover:bg-dark-border transition-colors min-w-[140px]"
              >
                <span className="font-bold">{selectedSymbol.replace('/USDT', '')}</span>
                <span className="text-gray-400 text-sm">/USDT</span>
                <svg className="w-4 h-4 text-gray-400 ml-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Symbol Dropdown */}
              {showSymbolDropdown && (
                <div className="absolute top-full left-0 mt-2 w-72 bg-dark-card border border-dark-border rounded-xl shadow-xl z-50 max-h-96 overflow-hidden">
                  {/* Search Input */}
                  <div className="p-3 border-b border-dark-border">
                    <input
                      type="text"
                      placeholder="Search symbol..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full px-3 py-2 bg-dark-surface rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-blue"
                      autoFocus
                    />
                  </div>

                  {/* Symbol List */}
                  <div className="max-h-72 overflow-y-auto">
                    {searchQuery ? (
                      // Show filtered results
                      <div className="p-2">
                        {filteredSymbols.length > 0 ? (
                          filteredSymbols.map(symbol => (
                            <button
                              key={symbol}
                              onClick={() => {
                                setSelectedSymbol(symbol)
                                setShowSymbolDropdown(false)
                                setSearchQuery('')
                              }}
                              className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                                selectedSymbol === symbol
                                  ? 'bg-accent-blue text-white'
                                  : 'hover:bg-dark-surface text-gray-300'
                              }`}
                            >
                              <span className="font-medium">{symbol.replace('/USDT', '')}</span>
                              <span className="text-gray-500 text-sm">/USDT</span>
                            </button>
                          ))
                        ) : (
                          <p className="text-gray-500 text-center py-4">No symbols found</p>
                        )}
                      </div>
                    ) : (
                      // Show grouped symbols
                      Object.entries(SYMBOL_GROUPS).map(([group, symbols]) => (
                        <div key={group} className="p-2">
                          <p className="text-xs text-gray-500 uppercase px-3 py-1">{group}</p>
                          {symbols.map(symbol => (
                            <button
                              key={symbol}
                              onClick={() => {
                                setSelectedSymbol(symbol)
                                setShowSymbolDropdown(false)
                              }}
                              className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                                selectedSymbol === symbol
                                  ? 'bg-accent-blue text-white'
                                  : 'hover:bg-dark-surface text-gray-300'
                              }`}
                            >
                              <span className="font-medium">{symbol.replace('/USDT', '')}</span>
                              <span className="text-gray-500 text-sm">/USDT</span>
                            </button>
                          ))}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Timeframe Selector */}
            <div className="flex items-center bg-dark-surface rounded-lg p-1">
              {TIMEFRAMES.map(tf => (
                <button
                  key={tf.value}
                  onClick={() => setSelectedTimeframe(tf.value)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    selectedTimeframe === tf.value
                      ? 'bg-accent-blue text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {tf.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Click outside to close dropdown */}
      {showSymbolDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowSymbolDropdown(false)}
        />
      )}

      <main className="p-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Left Column - Chart and Signals */}
          <div className="col-span-12 lg:col-span-8 space-y-6">
            {/* Price Info Bar */}
            <div className="bg-dark-card rounded-xl p-4 border border-dark-border">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold">{selectedSymbol}</h2>
                  <p className="text-3xl font-bold mt-1">
                    ${currentTicker.last?.toLocaleString() || '-'}
                  </p>
                </div>
                <div className="grid grid-cols-4 gap-6 text-sm">
                  <div>
                    <p className="text-gray-400">24h Change</p>
                    <p className={currentTicker.change_24h >= 0 ? 'text-accent-green' : 'text-accent-red'}>
                      {formatPercent(currentTicker.change_24h)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-400">24h High</p>
                    <p>${currentTicker.high_24h?.toLocaleString() || '-'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">24h Low</p>
                    <p>${currentTicker.low_24h?.toLocaleString() || '-'}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">24h Volume</p>
                    <p>{formatCurrency(currentTicker.volume_24h, selectedSymbol.split('/')[0])}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Price Chart */}
            <div className="bg-dark-card rounded-xl border border-dark-border overflow-hidden">
              <div className="p-4 border-b border-dark-border flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold">Price Chart</h3>
                  <span className="text-sm text-gray-400">{selectedSymbol} • {selectedTimeframe.toUpperCase()}</span>
                </div>
                {loading && (
                  <div className="flex items-center gap-2 text-accent-blue text-sm">
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Loading...
                  </div>
                )}
              </div>
              <div className="h-[500px]">
                <PriceChart
                  data={ohlcvData}
                  symbol={selectedSymbol}
                  timeframe={selectedTimeframe}
                  indicators={analysis?.indicators}
                />
              </div>
            </div>

            {/* Indicator Gauges */}
            <div className="bg-dark-card rounded-xl p-4 border border-dark-border">
              <h3 className="font-semibold mb-4">Technical Indicators</h3>
              <IndicatorGauge indicators={analysis?.indicators} />
            </div>

            {/* Trade Proposals */}
            <div className="bg-dark-card rounded-xl p-4 border border-dark-border">
              <h3 className="font-semibold mb-4">Trade Signals</h3>
              <div className="space-y-3">
                {currentSignals.length > 0 ? (
                  currentSignals.map((signal, idx) => (
                    <TradeProposal
                      key={idx}
                      signal={signal}
                      onExecute={onExecuteTrade}
                    />
                  ))
                ) : (
                  <p className="text-gray-400 text-center py-4">No active signals</p>
                )}
              </div>
            </div>

            {/* Market Structure */}
            <MarketStructure
              smc={analysis?.smc}
              structure={analysis?.structure}
            />
          </div>

          {/* Right Column - Portfolio and History */}
          <div className="col-span-12 lg:col-span-4 space-y-6">
            {/* Portfolio Summary */}
            <Portfolio
              portfolio={portfolio}
              positions={positions}
              tickers={tickers}
              onClosePosition={onClosePosition}
            />

            {/* Risk Status */}
            {riskData && (
              <div className="bg-dark-card rounded-xl p-4 border border-dark-border">
                <h3 className="font-semibold mb-4">Risk Status</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Daily P&L</span>
                    <span className={riskData.daily_pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}>
                      {formatCurrency(riskData.daily_pnl)} ({riskData.daily_pnl_percent}%)
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Consecutive Losses</span>
                    <span className={riskData.consecutive_losses >= 2 ? 'text-accent-yellow' : ''}>
                      {riskData.consecutive_losses}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Status</span>
                    <span className={riskData.is_paused ? 'text-accent-red' : 'text-accent-green'}>
                      {riskData.is_paused ? 'Paused' : 'Active'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* On-Chain Metrics */}
            <OnChainMetrics symbol={selectedSymbol} />

            {/* Trade History */}
            <TradeHistory trades={trades} />
          </div>
        </div>
      </main>
    </div>
  )
}
