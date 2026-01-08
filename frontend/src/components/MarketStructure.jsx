export default function MarketStructure({ smc, structure }) {
  if (!smc && !structure) {
    return (
      <div className="bg-dark-card rounded-xl border border-dark-border p-4">
        <h3 className="font-semibold mb-4">Market Structure (SMC)</h3>
        <p className="text-center text-gray-500 py-4">Loading analysis...</p>
      </div>
    )
  }

  const getBiasColor = (bias) => {
    if (bias === 1 || bias === 'bullish') return 'text-accent-green'
    if (bias === -1 || bias === 'bearish') return 'text-accent-red'
    return 'text-gray-400'
  }

  const getBiasLabel = (bias) => {
    if (bias === 1 || bias === 'bullish') return 'Bullish'
    if (bias === -1 || bias === 'bearish') return 'Bearish'
    return 'Neutral'
  }

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border p-4">
      <h3 className="font-semibold mb-4">Market Structure (SMC/ICT)</h3>

      <div className="grid grid-cols-2 gap-4">
        {/* Market Bias */}
        <div className="bg-dark-surface rounded-lg p-3">
          <span className="text-sm text-gray-400">Market Bias</span>
          <p className={`font-bold text-lg ${getBiasColor(structure?.bias || smc?.market_bias)}`}>
            {getBiasLabel(structure?.bias || smc?.market_bias)}
          </p>
        </div>

        {/* Trend */}
        <div className="bg-dark-surface rounded-lg p-3">
          <span className="text-sm text-gray-400">Trend</span>
          <p className={`font-bold text-lg ${getBiasColor(structure?.trend)}`}>
            {structure?.trend === 'uptrend' ? 'Uptrend' :
             structure?.trend === 'downtrend' ? 'Downtrend' :
             'Ranging'}
          </p>
        </div>

        {/* Swing Points */}
        <div className="bg-dark-surface rounded-lg p-3">
          <span className="text-sm text-gray-400">Swing Highs</span>
          <p className="font-semibold">{smc?.swing_highs_count || 0}</p>
        </div>

        <div className="bg-dark-surface rounded-lg p-3">
          <span className="text-sm text-gray-400">Swing Lows</span>
          <p className="font-semibold">{smc?.swing_lows_count || 0}</p>
        </div>
      </div>

      {/* Order Blocks */}
      <div className="mt-4">
        <h4 className="text-sm text-gray-400 mb-2">Order Blocks</h4>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-dark-surface rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-3 h-3 rounded bg-accent-green"></span>
              <span className="text-sm">Bullish OB</span>
            </div>
            <p className="font-semibold text-lg">{smc?.active_bullish_ob || 0}</p>
            <p className="text-xs text-gray-500">Active zones</p>
          </div>
          <div className="bg-dark-surface rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-3 h-3 rounded bg-accent-red"></span>
              <span className="text-sm">Bearish OB</span>
            </div>
            <p className="font-semibold text-lg">{smc?.active_bearish_ob || 0}</p>
            <p className="text-xs text-gray-500">Active zones</p>
          </div>
        </div>
      </div>

      {/* Fair Value Gaps */}
      <div className="mt-4">
        <h4 className="text-sm text-gray-400 mb-2">Fair Value Gaps</h4>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-dark-surface rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-3 h-3 rounded bg-accent-green"></span>
              <span className="text-sm">Bullish FVG</span>
            </div>
            <p className="font-semibold text-lg">{smc?.active_bullish_fvg || 0}</p>
            <p className="text-xs text-gray-500">Unfilled gaps</p>
          </div>
          <div className="bg-dark-surface rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-3 h-3 rounded bg-accent-red"></span>
              <span className="text-sm">Bearish FVG</span>
            </div>
            <p className="font-semibold text-lg">{smc?.active_bearish_fvg || 0}</p>
            <p className="text-xs text-gray-500">Unfilled gaps</p>
          </div>
        </div>
      </div>

      {/* Structure Breaks */}
      <div className="mt-4">
        <h4 className="text-sm text-gray-400 mb-2">Structure Events</h4>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-dark-surface rounded-lg p-3">
            <span className="text-sm text-gray-400">BOS Count</span>
            <p className="font-semibold">{smc?.recent_bos || 0}</p>
            <p className="text-xs text-gray-500">Break of Structure</p>
          </div>
          <div className="bg-dark-surface rounded-lg p-3">
            <span className="text-sm text-gray-400">CHoCH Count</span>
            <p className="font-semibold">{smc?.recent_choch || 0}</p>
            <p className="text-xs text-gray-500">Change of Character</p>
          </div>
        </div>
      </div>

      {/* Support/Resistance Levels */}
      {structure?.support_levels && structure?.resistance_levels && (
        <div className="mt-4">
          <h4 className="text-sm text-gray-400 mb-2">Key Levels</h4>
          <div className="space-y-2">
            {structure.resistance_levels.slice(0, 2).map((level, idx) => (
              <div key={`r-${idx}`} className="flex items-center justify-between text-sm">
                <span className="text-accent-red">R{idx + 1}</span>
                <span className="font-medium">${level.toLocaleString()}</span>
              </div>
            ))}
            {structure.support_levels.slice(0, 2).map((level, idx) => (
              <div key={`s-${idx}`} className="flex items-center justify-between text-sm">
                <span className="text-accent-green">S{idx + 1}</span>
                <span className="font-medium">${level.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Kill Zone Status */}
      {smc?.in_kill_zone !== undefined && (
        <div className="mt-4 bg-dark-surface rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Kill Zone</span>
            {smc.in_kill_zone ? (
              <span className="text-accent-green font-medium">
                Active ({smc.kill_zone_name})
              </span>
            ) : (
              <span className="text-gray-500">Not Active</span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Optimal trading windows: London (2-5 AM EST), NY (7-10 AM EST)
          </p>
        </div>
      )}
    </div>
  )
}
