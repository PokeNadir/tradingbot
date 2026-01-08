import { useState, useCallback } from 'react'
import { fetchAPI } from '../utils/api'

export function useTrading() {
  const [portfolio, setPortfolio] = useState(null)
  const [positions, setPositions] = useState([])
  const [signals, setSignals] = useState([])
  const [tickers, setTickers] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchPortfolio = useCallback(async () => {
    try {
      const data = await fetchAPI('/api/portfolio')
      setPortfolio(data)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  const fetchPositions = useCallback(async () => {
    try {
      const data = await fetchAPI('/api/positions')
      setPositions(data.positions || [])
    } catch (e) {
      setError(e.message)
    }
  }, [])

  const fetchSignals = useCallback(async (symbol) => {
    setLoading(true)
    try {
      const data = await fetchAPI(`/api/signals/${symbol}`)
      setSignals(data.signals || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const executeTrade = useCallback(async (signal) => {
    setLoading(true)
    try {
      const data = await fetchAPI('/api/execute', {
        method: 'POST',
        body: JSON.stringify(signal)
      })
      await fetchPortfolio()
      await fetchPositions()
      return data
    } catch (e) {
      setError(e.message)
      throw e
    } finally {
      setLoading(false)
    }
  }, [fetchPortfolio, fetchPositions])

  const closePosition = useCallback(async (positionId, currentPrice) => {
    setLoading(true)
    try {
      const data = await fetchAPI(`/api/close/${positionId}?current_price=${currentPrice}`, {
        method: 'POST'
      })
      await fetchPortfolio()
      await fetchPositions()
      return data
    } catch (e) {
      setError(e.message)
      throw e
    } finally {
      setLoading(false)
    }
  }, [fetchPortfolio, fetchPositions])

  const updateData = useCallback((wsData) => {
    if (wsData.ticker) {
      setTickers(prev => ({
        ...prev,
        [wsData.symbol]: wsData.ticker
      }))
    }
    if (wsData.signals) {
      setSignals(wsData.signals)
    }
    if (wsData.portfolio) {
      setPortfolio(wsData.portfolio)
    }
  }, [])

  return {
    portfolio,
    positions,
    signals,
    tickers,
    loading,
    error,
    fetchPortfolio,
    fetchPositions,
    fetchSignals,
    executeTrade,
    closePosition,
    updateData
  }
}

export default useTrading
