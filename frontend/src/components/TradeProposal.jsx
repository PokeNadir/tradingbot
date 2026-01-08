import { useState } from 'react'
import { formatCurrency, formatPercent, getSignalStrengthColor, getRiskColor } from '../utils/calculations'

export default function TradeProposal({ signal, onExecute }) {
  const [executing, setExecuting] = useState(false)
  const [confirmed, setConfirmed] = useState(false)

  const handleExecute = async () => {
    if (!confirmed) {
      setConfirmed(true)
      return
    }

    setExecuting(true)
    try {
      await onExecute(signal)
    } catch (error) {
      console.error('Trade execution failed:', error)
    } finally {
      setExecuting(false)
      setConfirmed(false)
    }
  }

  const handleCancel = () => {
    setConfirmed(false)
  }

  const isLong = signal.direction === 'long'
  const directionColor = isLong ? 'text-accent-green' : 'text-accent-red'
  const directionBg = isLong ? 'bg-accent-green/10' : 'bg-accent-red/10'
  const directionBorder = isLong ? 'border-accent-green/30' : 'border-accent-red/30'

  return (
    <div className={`rounded-lg border ${directionBorder} ${directionBg} p-4`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className={`font-bold text-lg ${directionColor}`}>
              {isLong ? 'LONG' : 'SHORT'}
            </span>
            <span className="text-white font-semibold">{signal.symbol}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              signal.strategy === 'mean_reversion' ? 'bg-purple-500/20 text-purple-400' :
              signal.strategy === 'ema_crossover' ? 'bg-blue-500/20 text-blue-400' :
              signal.strategy === 'breakout' ? 'bg-orange-500/20 text-orange-400' :
              'bg-gray-500/20 text-gray-400'
            }`}>
              {signal.strategy?.replace('_', ' ').toUpperCase()}
            </span>
          </div>
          <p className="text-gray-400 text-sm mt-1">{signal.reason}</p>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1">
            <span className="text-gray-400 text-sm">Strength:</span>
            <span className={`font-semibold ${getSignalStrengthColor(signal.strength)}`}>
              {Math.round(signal.strength * 100)}%
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-4 text-sm">
        <div>
          <p className="text-gray-400">Entry</p>
          <p className="font-medium">${signal.entry_price?.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-gray-400">Stop Loss</p>
          <p className="font-medium text-accent-red">${signal.stop_loss?.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-gray-400">Take Profit</p>
          <p className="font-medium text-accent-green">${signal.take_profit?.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-gray-400">Risk/Reward</p>
          <p className="font-medium">{signal.risk_reward?.toFixed(2)}:1</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
        <div>
          <p className="text-gray-400">Position Size</p>
          <p className="font-medium">{signal.position_size?.toFixed(4)} {signal.symbol?.split('/')[0]}</p>
        </div>
        <div>
          <p className="text-gray-400">Size (USDT)</p>
          <p className="font-medium">{formatCurrency(signal.position_size_quote)}</p>
        </div>
        <div>
          <p className="text-gray-400">Risk</p>
          <p className={`font-medium ${getRiskColor(signal.risk_percent * 100)}`}>
            {formatPercent(signal.risk_percent * 100)} ({formatCurrency(signal.risk_amount)})
          </p>
        </div>
      </div>

      {/* Confirmations */}
      {signal.confirmations && signal.confirmations.length > 0 && (
        <div className="mb-4">
          <p className="text-gray-400 text-sm mb-2">Confirmations:</p>
          <div className="flex flex-wrap gap-2">
            {signal.confirmations.map((conf, idx) => (
              <span key={idx} className="text-xs px-2 py-1 bg-dark-surface rounded text-gray-300">
                {conf}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Execute Button */}
      <div className="flex gap-2">
        {confirmed ? (
          <>
            <button
              onClick={handleExecute}
              disabled={executing}
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                isLong
                  ? 'bg-accent-green hover:bg-accent-green/80 text-white'
                  : 'bg-accent-red hover:bg-accent-red/80 text-white'
              } disabled:opacity-50`}
            >
              {executing ? 'Executing...' : 'Confirm Trade'}
            </button>
            <button
              onClick={handleCancel}
              className="py-2 px-4 rounded-lg font-medium bg-dark-surface hover:bg-dark-border text-gray-300"
            >
              Cancel
            </button>
          </>
        ) : (
          <button
            onClick={handleExecute}
            className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
              isLong
                ? 'bg-accent-green/20 hover:bg-accent-green/30 text-accent-green border border-accent-green/30'
                : 'bg-accent-red/20 hover:bg-accent-red/30 text-accent-red border border-accent-red/30'
            }`}
          >
            Execute {isLong ? 'Long' : 'Short'}
          </button>
        )}
      </div>
    </div>
  )
}
