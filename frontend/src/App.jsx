import React, { useState, useEffect } from 'react'
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
  }, [connected])

  useEffect(() => {
    if (data) {
      if (data.type === 'update') {
        trading.updateData(data)
      }
    }
  }, [data])

  return (
    <div className="min-h-screen bg-dark-900">
      <header className="bg-dark-800 border-b border-dark-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-white">Trading Bot</h1>
            <span className="px-2 py-1 text-xs bg-accent-green/20 text-accent-green rounded">
              Paper Trading
            </span>
          </div>
          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 text-sm ${connected ? 'text-accent-green' : 'text-accent-red'}`}>
              <span className={`w-2 h-2 rounded-full ${connected ? 'bg-accent-green' : 'bg-accent-red'}`}></span>
              {connected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>
      </header>

      <main className="p-6">
        <Dashboard
          trading={trading}
          wsData={data}
          onExecuteTrade={(signal) => send({ type: 'execute_trade', signal })}
          onClosePosition={(id, price) => send({ type: 'close_position', position_id: id, current_price: price })}
        />
      </main>
    </div>
  )
}

export default App
