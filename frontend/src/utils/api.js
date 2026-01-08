const API_BASE = ''

export async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  }

  const response = await fetch(url, { ...defaultOptions, ...options })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export async function getPortfolio() {
  return fetchAPI('/api/portfolio')
}

export async function getPositions() {
  return fetchAPI('/api/positions')
}

export async function getTrades(limit = 20) {
  return fetchAPI(`/api/trades?limit=${limit}`)
}

export async function getTicker(symbol) {
  return fetchAPI(`/api/ticker/${symbol}`)
}

export async function getOHLCV(symbol, timeframe = '15m', limit = 100) {
  return fetchAPI(`/api/ohlcv/${symbol}?timeframe=${timeframe}&limit=${limit}`)
}

export async function getSignals(symbol) {
  return fetchAPI(`/api/signals/${symbol}`)
}

export async function getAnalysis(symbol) {
  return fetchAPI(`/api/analysis/${symbol}`)
}

export async function executeTrade(signal) {
  return fetchAPI('/api/execute', {
    method: 'POST',
    body: JSON.stringify(signal)
  })
}

export async function closePosition(positionId, currentPrice) {
  return fetchAPI(`/api/close/${positionId}?current_price=${currentPrice}`, {
    method: 'POST'
  })
}

export async function closeAllPositions() {
  return fetchAPI('/api/close-all', { method: 'POST' })
}

export async function getRisk() {
  return fetchAPI('/api/risk')
}

export async function getPerformance() {
  return fetchAPI('/api/performance')
}
