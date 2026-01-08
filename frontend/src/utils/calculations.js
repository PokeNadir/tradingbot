export function formatCurrency(value, currency = 'USDT') {
  if (value === null || value === undefined) return '-'

  const absValue = Math.abs(value)

  if (absValue >= 1000000) {
    return `${(value / 1000000).toFixed(2)}M ${currency}`
  } else if (absValue >= 1000) {
    return `${(value / 1000).toFixed(2)}K ${currency}`
  } else {
    return `${value.toFixed(2)} ${currency}`
  }
}

export function formatPercent(value) {
  if (value === null || value === undefined) return '-'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

export function formatPrice(value, decimals = 2) {
  if (value === null || value === undefined) return '-'
  return value.toFixed(decimals)
}

export function formatNumber(value, decimals = 2) {
  if (value === null || value === undefined) return '-'
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

export function calculatePnL(entry, current, size, direction) {
  if (direction === 'long') {
    return (current - entry) * size
  } else {
    return (entry - current) * size
  }
}

export function calculatePnLPercent(entry, current, direction) {
  if (direction === 'long') {
    return ((current - entry) / entry) * 100
  } else {
    return ((entry - current) / entry) * 100
  }
}

export function getRiskColor(riskPercent) {
  if (riskPercent <= 1) return 'text-accent-green'
  if (riskPercent <= 2) return 'text-accent-yellow'
  return 'text-accent-red'
}

export function getSignalStrengthColor(strength) {
  if (strength >= 0.8) return 'text-accent-green'
  if (strength >= 0.6) return 'text-accent-yellow'
  return 'text-gray-400'
}

export function getPnLColor(pnl) {
  if (pnl > 0) return 'text-accent-green'
  if (pnl < 0) return 'text-accent-red'
  return 'text-gray-400'
}

export function timeAgo(timestamp) {
  const now = new Date()
  const time = new Date(timestamp)
  const diff = now - time

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (days > 0) return `${days}d ago`
  if (hours > 0) return `${hours}h ago`
  if (minutes > 0) return `${minutes}m ago`
  return 'just now'
}
