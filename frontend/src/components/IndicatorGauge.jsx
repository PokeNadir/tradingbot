export default function IndicatorGauge({ indicators }) {
  if (!indicators) {
    return (
      <div className="text-center text-gray-400 py-4">
        Loading indicators...
      </div>
    )
  }

  const gauges = [
    {
      name: 'RSI',
      value: indicators.rsi,
      min: 0,
      max: 100,
      zones: [
        { max: 30, color: 'bg-accent-green', label: 'Oversold' },
        { max: 70, color: 'bg-gray-500', label: 'Neutral' },
        { max: 100, color: 'bg-accent-red', label: 'Overbought' },
      ],
    },
    {
      name: 'Stoch K',
      value: indicators.stoch_k,
      min: 0,
      max: 100,
      zones: [
        { max: 20, color: 'bg-accent-green', label: 'Oversold' },
        { max: 80, color: 'bg-gray-500', label: 'Neutral' },
        { max: 100, color: 'bg-accent-red', label: 'Overbought' },
      ],
    },
    {
      name: 'ADX',
      value: indicators.adx,
      min: 0,
      max: 100,
      zones: [
        { max: 20, color: 'bg-gray-500', label: 'Weak' },
        { max: 40, color: 'bg-accent-yellow', label: 'Trending' },
        { max: 100, color: 'bg-accent-green', label: 'Strong' },
      ],
    },
  ]

  const getZoneColor = (value, zones) => {
    for (const zone of zones) {
      if (value <= zone.max) {
        return zone.color
      }
    }
    return 'bg-gray-500'
  }

  const getZoneLabel = (value, zones) => {
    for (const zone of zones) {
      if (value <= zone.max) {
        return zone.label
      }
    }
    return 'N/A'
  }

  return (
    <div className="space-y-6">
      {/* Gauges */}
      <div className="grid grid-cols-3 gap-4">
        {gauges.map(gauge => (
          <div key={gauge.name} className="bg-dark-surface rounded-lg p-3">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-400">{gauge.name}</span>
              <span className="font-semibold">
                {gauge.value?.toFixed(1) || '-'}
              </span>
            </div>
            <div className="h-2 bg-dark-bg rounded-full overflow-hidden">
              <div
                className={`h-full ${getZoneColor(gauge.value, gauge.zones)} transition-all duration-300`}
                style={{ width: `${Math.min(100, Math.max(0, (gauge.value / gauge.max) * 100))}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {getZoneLabel(gauge.value, gauge.zones)}
            </div>
          </div>
        ))}
      </div>

      {/* MACD */}
      <div className="bg-dark-surface rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">MACD</span>
          <div className="flex items-center gap-4 text-sm">
            <span>
              <span className="text-gray-500">Line:</span>{' '}
              <span className={indicators.macd >= 0 ? 'text-accent-green' : 'text-accent-red'}>
                {indicators.macd?.toFixed(2) || '-'}
              </span>
            </span>
            <span>
              <span className="text-gray-500">Signal:</span>{' '}
              <span className="text-accent-yellow">{indicators.macd_signal?.toFixed(2) || '-'}</span>
            </span>
            <span>
              <span className="text-gray-500">Hist:</span>{' '}
              <span className={indicators.macd_histogram >= 0 ? 'text-accent-green' : 'text-accent-red'}>
                {indicators.macd_histogram?.toFixed(2) || '-'}
              </span>
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-4 bg-dark-bg rounded overflow-hidden flex">
            {indicators.macd_histogram && (
              <div
                className={`h-full ${indicators.macd_histogram >= 0 ? 'bg-accent-green' : 'bg-accent-red'}`}
                style={{
                  width: `${Math.min(100, Math.abs(indicators.macd_histogram) * 10)}%`,
                  marginLeft: indicators.macd_histogram >= 0 ? '50%' : `${50 - Math.min(50, Math.abs(indicators.macd_histogram) * 10)}%`,
                }}
              />
            )}
          </div>
        </div>
      </div>

      {/* Bollinger Bands */}
      <div className="bg-dark-surface rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">Bollinger Bands</span>
          {indicators.bb_squeeze && (
            <span className="text-xs px-2 py-0.5 bg-accent-yellow/20 text-accent-yellow rounded">
              SQUEEZE
            </span>
          )}
        </div>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Upper:</span>{' '}
            <span className="text-purple-400">${indicators.bb_upper?.toLocaleString() || '-'}</span>
          </div>
          <div>
            <span className="text-gray-500">Middle:</span>{' '}
            <span className="text-gray-300">${indicators.bb_middle?.toLocaleString() || '-'}</span>
          </div>
          <div>
            <span className="text-gray-500">Lower:</span>{' '}
            <span className="text-purple-400">${indicators.bb_lower?.toLocaleString() || '-'}</span>
          </div>
        </div>
      </div>

      {/* EMAs */}
      <div className="bg-dark-surface rounded-lg p-3">
        <div className="text-sm text-gray-400 mb-2">Moving Averages</div>
        <div className="grid grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">EMA 9:</span>{' '}
            <span className="text-yellow-400">${indicators.ema_9?.toLocaleString() || '-'}</span>
          </div>
          <div>
            <span className="text-gray-500">EMA 21:</span>{' '}
            <span className="text-orange-400">${indicators.ema_21?.toLocaleString() || '-'}</span>
          </div>
          <div>
            <span className="text-gray-500">EMA 50:</span>{' '}
            <span className="text-blue-400">${indicators.ema_50?.toLocaleString() || '-'}</span>
          </div>
          <div>
            <span className="text-gray-500">SMA 200:</span>{' '}
            <span className="text-cyan-400">${indicators.sma_200?.toLocaleString() || '-'}</span>
          </div>
        </div>
        <div className="mt-2 text-xs">
          <span className="text-gray-500">Trend Bias:</span>{' '}
          <span className={indicators.trend_bias > 0 ? 'text-accent-green' : indicators.trend_bias < 0 ? 'text-accent-red' : 'text-gray-400'}>
            {indicators.trend_bias > 0 ? 'Bullish (Above SMA 200)' : indicators.trend_bias < 0 ? 'Bearish (Below SMA 200)' : 'Neutral'}
          </span>
        </div>
      </div>

      {/* ATR */}
      <div className="bg-dark-surface rounded-lg p-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">ATR (14)</span>
          <div className="text-sm">
            <span className="font-semibold">${indicators.atr?.toFixed(2) || '-'}</span>
            <span className="text-gray-500 ml-2">
              ({indicators.atr_percent?.toFixed(2) || '-'}%)
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
