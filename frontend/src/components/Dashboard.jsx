import { useState, useEffect } from 'react'
import PriceChart from './PriceChart'
import TradeProposal from './TradeProposal'
import IndicatorGauge from './IndicatorGauge'
import Portfolio from './Portfolio'
import TradeHistory from './TradeHistory'
import OnChainMetrics from './OnChainMetrics'
import MarketStructure from './MarketStructure'
import { formatCurrency, formatPercent } from '../utils/calculations'

const SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

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
  const [ohlcvData, setOhlcvData] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [trades, setTrades] = useState([])
  const [riskData, setRiskData] = useState(null)
  const [loading, setLoading] = useState(false)

  // Fetch OHLCV data when symbol changes
  useEffect(() => {
    fetchOHLCV()
    fetchAnalysis()
  }, [selectedSymbol])

  // Fetch trade history on mount
  useEffect(() => {
    fetchTrades()
    fetchRisk()
  }, [])

  async function fetchOHLCV() {
    try {
      const [base, quote] = selectedSymbol.split('/')
      const response = await fetch(`/api/ohlcv/${base}/${quote}?timeframe=15m&limit=200`)
      if (response.ok) {
        const data = await response.json()
        setOhlcvData(data.ohlcv || [])
      }
    } catch (error) {
      console.error('Error fetching OHLCV:', error)
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

          {/* Symbol Selector */}
          <div className="flex items-center gap-2">
            {SYMBOLS.map(symbol => (
              <button
                key={symbol}
                onClick={() => setSelectedSymbol(symbol)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedSymbol === symbol
                    ? 'bg-accent-blue text-white'
                    : 'bg-dark-surface text-gray-400 hover:text-white hover:bg-dark-border'
                }`}
              >
                {symbol.replace('/USDT', '')}
              </button>
            ))}
          </div>
        </div>
      </header>

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
              <div className="p-4 border-b border-dark-border">
                <h3 className="font-semibold">Price Chart</h3>
              </div>
              <div className="h-96">
                <PriceChart
                  data={ohlcvData}
                  symbol={selectedSymbol}
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
