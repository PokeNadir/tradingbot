import React, { useEffect, useRef } from 'react'
import Dashboard from './components/Dashboard'
import { useWebSocket } from './hooks/useWebSocket'
import { useTrading } from './hooks/useTrading'

const WS_URL = `ws://${window.location.hostname}:8000/ws`

function App() {
  const { connected, data, send } = useWebSocket(WS_URL)
  const trading = useTrading()
  const hasSubscribed = useRef(false)

  // Subscribe once when connected
  useEffect(() => {
    if (connected && !hasSubscribed.current) {
      send({ type: 'subscribe', symbols: ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'] })
      hasSubscribed.current = true
    }
    if (!connected) {
      hasSubscribed.current = false
    }
  }, [connected, send])

  // Handle incoming WebSocket data - use updateData directly to avoid infinite loop
  useEffect(() => {
    if (data && data.type === 'update') {
      trading.updateData(data)
    }
  }, [data, trading.updateData])

  return (
    <Dashboard
      portfolio={trading.portfolio}
      positions={trading.positions}
      signals={trading.signals}
      tickers={trading.tickers}
      connected={connected}
      onExecuteTrade={(signal) => send({ type: 'execute_trade', signal })}
      onClosePosition={(id, price) => send({ type: 'close_position', position_id: id, current_price: price })}
    />
  )
}

export default App
