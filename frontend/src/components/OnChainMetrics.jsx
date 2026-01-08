import { useState, useEffect } from 'react'

export default function OnChainMetrics({ symbol }) {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    // On-chain metrics are optional and may not be available
    // This component shows placeholder if not configured
  }, [symbol])

  // MVRV interpretation
  const getMvrvSignal = (mvrv) => {
    if (!mvrv) return { signal: 'N/A', color: 'text-gray-400' }
    if (mvrv >= 3.5) return { signal: 'Extreme Euphoria - SELL', color: 'text-accent-red' }
    if (mvrv >= 2.4) return { signal: 'Overheated - Take Profits', color: 'text-accent-yellow' }
    if (mvrv >= 1.0) return { signal: 'Neutral', color: 'text-gray-400' }
    if (mvrv >= 0.8) return { signal: 'Undervalued - Accumulate', color: 'text-accent-green' }
    return { signal: 'Capitulation - STRONG BUY', color: 'text-accent-green' }
  }

  // NUPL interpretation
  const getNuplSignal = (nupl) => {
    if (!nupl && nupl !== 0) return { signal: 'N/A', color: 'text-gray-400' }
    if (nupl >= 0.75) return { signal: 'Euphoria - SELL', color: 'text-accent-red' }
    if (nupl >= 0.5) return { signal: 'Belief - Reduce Exposure', color: 'text-accent-yellow' }
    if (nupl >= 0.25) return { signal: 'Optimism', color: 'text-gray-400' }
    if (nupl >= 0) return { signal: 'Hope', color: 'text-gray-400' }
    return { signal: 'Capitulation - BUY', color: 'text-accent-green' }
  }

  // Funding rate interpretation
  const getFundingSignal = (funding) => {
    if (!funding && funding !== 0) return { signal: 'N/A', color: 'text-gray-400' }
    if (funding > 0.001) return { signal: 'Extreme Long - Correction Risk', color: 'text-accent-red' }
    if (funding > 0.0005) return { signal: 'Longs Dominant - Caution', color: 'text-accent-yellow' }
    if (funding < 0) return { signal: 'Shorts Dominant - Squeeze Setup', color: 'text-accent-green' }
    return { signal: 'Neutral', color: 'text-gray-400' }
  }

  // Placeholder metrics for demo
  const demoMetrics = {
    mvrv: 1.8,
    nupl: 0.35,
    funding: 0.0003,
    exchange_netflow: -1250,
    whale_transactions: 45,
    last_updated: new Date().toISOString()
  }

  const displayMetrics = metrics || demoMetrics
  const mvrvSignal = getMvrvSignal(displayMetrics.mvrv)
  const nuplSignal = getNuplSignal(displayMetrics.nupl)
  const fundingSignal = getFundingSignal(displayMetrics.funding)

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">On-Chain Metrics</h3>
        {!metrics && (
          <span className="text-xs px-2 py-0.5 bg-accent-yellow/20 text-accent-yellow rounded">
            Demo Data
          </span>
        )}
      </div>

      <div className="space-y-4">
        {/* MVRV Ratio */}
        <div className="bg-dark-surface rounded-lg p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-400">MVRV Ratio</span>
            <span className="font-semibold">{displayMetrics.mvrv?.toFixed(2) || '-'}</span>
          </div>
          <div className="h-2 bg-dark-bg rounded-full overflow-hidden mb-1">
            <div
              className={`h-full transition-all ${
                displayMetrics.mvrv >= 3.5 ? 'bg-accent-red' :
                displayMetrics.mvrv >= 2.4 ? 'bg-accent-yellow' :
                displayMetrics.mvrv >= 1.0 ? 'bg-gray-500' :
                'bg-accent-green'
              }`}
              style={{ width: `${Math.min(100, (displayMetrics.mvrv / 4) * 100)}%` }}
            />
          </div>
          <p className={`text-xs ${mvrvSignal.color}`}>{mvrvSignal.signal}</p>
        </div>

        {/* NUPL */}
        <div className="bg-dark-surface rounded-lg p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-400">NUPL</span>
            <span className="font-semibold">{displayMetrics.nupl?.toFixed(2) || '-'}</span>
          </div>
          <div className="h-2 bg-dark-bg rounded-full overflow-hidden mb-1">
            <div
              className={`h-full transition-all ${
                displayMetrics.nupl >= 0.75 ? 'bg-accent-red' :
                displayMetrics.nupl >= 0.5 ? 'bg-accent-yellow' :
                displayMetrics.nupl >= 0 ? 'bg-gray-500' :
                'bg-accent-green'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, (displayMetrics.nupl + 0.25) * 80))}%` }}
            />
          </div>
          <p className={`text-xs ${nuplSignal.color}`}>{nuplSignal.signal}</p>
        </div>

        {/* Funding Rate */}
        <div className="bg-dark-surface rounded-lg p-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-400">Funding Rate (8h)</span>
            <span className={`font-semibold ${
              displayMetrics.funding > 0 ? 'text-accent-green' : 'text-accent-red'
            }`}>
              {displayMetrics.funding ? `${(displayMetrics.funding * 100).toFixed(4)}%` : '-'}
            </span>
          </div>
          <p className={`text-xs ${fundingSignal.color}`}>{fundingSignal.signal}</p>
        </div>

        {/* Exchange Netflow */}
        <div className="bg-dark-surface rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Exchange Netflow</span>
            <div className="text-right">
              <span className={`font-semibold ${
                displayMetrics.exchange_netflow < 0 ? 'text-accent-green' : 'text-accent-red'
              }`}>
                {displayMetrics.exchange_netflow > 0 ? '+' : ''}
                {displayMetrics.exchange_netflow?.toLocaleString() || '-'} BTC
              </span>
              <p className={`text-xs ${
                displayMetrics.exchange_netflow < 0 ? 'text-accent-green' : 'text-accent-red'
              }`}>
                {displayMetrics.exchange_netflow < 0 ? 'Outflow (Bullish)' : 'Inflow (Bearish)'}
              </p>
            </div>
          </div>
        </div>

        {/* Whale Transactions */}
        <div className="bg-dark-surface rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Whale Txns (24h)</span>
            <span className="font-semibold">{displayMetrics.whale_transactions || '-'}</span>
          </div>
        </div>
      </div>

      {displayMetrics.last_updated && (
        <p className="text-xs text-gray-500 mt-3 text-center">
          Updated: {new Date(displayMetrics.last_updated).toLocaleTimeString()}
        </p>
      )}
    </div>
  )
}
