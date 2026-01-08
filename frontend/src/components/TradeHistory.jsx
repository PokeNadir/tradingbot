import { formatCurrency, formatPercent, getPnLColor, timeAgo } from '../utils/calculations'

export default function TradeHistory({ trades }) {
  if (!trades || trades.length === 0) {
    return (
      <div className="bg-dark-card rounded-xl border border-dark-border p-4">
        <h3 className="font-semibold mb-4">Trade History</h3>
        <p className="text-center text-gray-500 py-4">No trades yet</p>
      </div>
    )
  }

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border">
      <div className="p-4 border-b border-dark-border">
        <h3 className="font-semibold">Trade History</h3>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {trades.map((trade, idx) => {
          const isLong = trade.direction === 'long'
          const isWin = trade.pnl > 0

          return (
            <div
              key={trade.id || idx}
              className={`p-3 border-b border-dark-border last:border-0 ${
                idx % 2 === 0 ? 'bg-dark-surface/30' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                    isLong ? 'bg-accent-green/20 text-accent-green' : 'bg-accent-red/20 text-accent-red'
                  }`}>
                    {isLong ? 'LONG' : 'SHORT'}
                  </span>
                  <span className="font-medium text-sm">{trade.symbol}</span>
                </div>
                <span className={`font-semibold ${getPnLColor(trade.pnl)}`}>
                  {formatCurrency(trade.pnl)}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
                <div>
                  <span>Entry:</span>{' '}
                  <span className="text-white">${trade.entry_price?.toLocaleString()}</span>
                </div>
                <div>
                  <span>Exit:</span>{' '}
                  <span className="text-white">${trade.exit_price?.toLocaleString()}</span>
                </div>
                <div>
                  <span>Size:</span>{' '}
                  <span className="text-white">{trade.size?.toFixed(4)}</span>
                </div>
                <div>
                  <span>Return:</span>{' '}
                  <span className={getPnLColor(trade.pnl_percent)}>
                    {formatPercent(trade.pnl_percent)}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between mt-2 text-xs">
                <span className="text-gray-500">{trade.strategy}</span>
                <span className="text-gray-500">{timeAgo(trade.exit_time || trade.timestamp)}</span>
              </div>

              {trade.exit_reason && (
                <div className="mt-1">
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    trade.exit_reason === 'take_profit' ? 'bg-accent-green/20 text-accent-green' :
                    trade.exit_reason === 'stop_loss' ? 'bg-accent-red/20 text-accent-red' :
                    'bg-gray-500/20 text-gray-400'
                  }`}>
                    {trade.exit_reason.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
