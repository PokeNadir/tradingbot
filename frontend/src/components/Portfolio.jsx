import { useState } from 'react'
import { formatCurrency, formatPercent, calculatePnL, calculatePnLPercent, getPnLColor } from '../utils/calculations'

export default function Portfolio({ portfolio, positions, tickers, onClosePosition }) {
  const [closingId, setClosingId] = useState(null)

  const handleClose = async (position) => {
    const ticker = tickers[position.symbol]
    if (!ticker) return

    setClosingId(position.id)
    try {
      await onClosePosition(position.id, ticker.last)
    } catch (error) {
      console.error('Failed to close position:', error)
    } finally {
      setClosingId(null)
    }
  }

  // Calculate total unrealized PnL
  const totalUnrealizedPnL = positions.reduce((total, pos) => {
    const ticker = tickers[pos.symbol]
    if (!ticker) return total
    const pnl = calculatePnL(pos.entry_price, ticker.last, pos.size, pos.direction)
    return total + pnl
  }, 0)

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border">
      {/* Portfolio Summary */}
      <div className="p-4 border-b border-dark-border">
        <h3 className="font-semibold mb-4">Portfolio</h3>

        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-gray-400">Balance</span>
            <span className="font-semibold">{formatCurrency(portfolio?.balance)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Equity</span>
            <span className="font-semibold">{formatCurrency(portfolio?.equity)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Unrealized P&L</span>
            <span className={`font-semibold ${getPnLColor(totalUnrealizedPnL)}`}>
              {formatCurrency(totalUnrealizedPnL)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Total P&L</span>
            <span className={`font-semibold ${getPnLColor(portfolio?.total_pnl)}`}>
              {formatCurrency(portfolio?.total_pnl)} ({formatPercent(portfolio?.total_pnl_percent)})
            </span>
          </div>
        </div>

        {/* Performance Stats */}
        {portfolio?.stats && (
          <div className="mt-4 pt-4 border-t border-dark-border grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-400">Win Rate</span>
              <p className="font-medium">{formatPercent(portfolio.stats.win_rate)}</p>
            </div>
            <div>
              <span className="text-gray-400">Total Trades</span>
              <p className="font-medium">{portfolio.stats.total_trades || 0}</p>
            </div>
            <div>
              <span className="text-gray-400">Avg Win</span>
              <p className="font-medium text-accent-green">{formatCurrency(portfolio.stats.avg_win)}</p>
            </div>
            <div>
              <span className="text-gray-400">Avg Loss</span>
              <p className="font-medium text-accent-red">{formatCurrency(portfolio.stats.avg_loss)}</p>
            </div>
          </div>
        )}
      </div>

      {/* Open Positions */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-sm text-gray-400">Open Positions ({positions.length})</h4>
        </div>

        {positions.length === 0 ? (
          <p className="text-center text-gray-500 py-4">No open positions</p>
        ) : (
          <div className="space-y-3">
            {positions.map(position => {
              const ticker = tickers[position.symbol]
              const currentPrice = ticker?.last || position.entry_price
              const pnl = calculatePnL(position.entry_price, currentPrice, position.size, position.direction)
              const pnlPercent = calculatePnLPercent(position.entry_price, currentPrice, position.direction)
              const isLong = position.direction === 'long'

              return (
                <div
                  key={position.id}
                  className="bg-dark-surface rounded-lg p-3"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                        isLong ? 'bg-accent-green/20 text-accent-green' : 'bg-accent-red/20 text-accent-red'
                      }`}>
                        {isLong ? 'LONG' : 'SHORT'}
                      </span>
                      <span className="font-medium">{position.symbol}</span>
                    </div>
                    <span className={`font-semibold ${getPnLColor(pnl)}`}>
                      {formatCurrency(pnl)} ({formatPercent(pnlPercent)})
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-xs text-gray-400 mb-2">
                    <div>
                      <span>Entry:</span>{' '}
                      <span className="text-white">${position.entry_price?.toLocaleString()}</span>
                    </div>
                    <div>
                      <span>Current:</span>{' '}
                      <span className="text-white">${currentPrice?.toLocaleString()}</span>
                    </div>
                    <div>
                      <span>Size:</span>{' '}
                      <span className="text-white">{position.size?.toFixed(4)}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-400 mb-3">
                    <div>
                      <span>SL:</span>{' '}
                      <span className="text-accent-red">${position.stop_loss?.toLocaleString()}</span>
                    </div>
                    <div>
                      <span>TP:</span>{' '}
                      <span className="text-accent-green">${position.take_profit?.toLocaleString()}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleClose(position)}
                    disabled={closingId === position.id}
                    className="w-full py-1.5 text-sm rounded bg-dark-border hover:bg-dark-bg text-gray-300 transition-colors disabled:opacity-50"
                  >
                    {closingId === position.id ? 'Closing...' : 'Close Position'}
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
