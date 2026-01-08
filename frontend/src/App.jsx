import React, { useEffect } from 'react'
import Dashboard from './components/Dashboard'
import { useWebSocket } from './hooks/useWebSocket'
import { useTrading } from './hooks/useTrading'

function App() {
  const { connected, data, send } = useWebSocket('ws://localhost:8000/ws')
  const trading = useTrading()

  useEffect(() => {
    if (connected) {
      send({ type: 'subscribe', symbols: ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'] })
    }
  }, [connected, send])

  useEffect(() => {
    if (data) {
      if (data.type === 'update') {
        trading.updateData(data)
      }
    }
  }, [data, trading])

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
