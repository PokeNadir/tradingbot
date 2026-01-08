import { useState, useEffect, useCallback, useRef } from 'react'

export function useWebSocket(url) {
  const [connected, setConnected] = useState(false)
  const [data, setData] = useState(null)
  const ws = useRef(null)
  const reconnectTimeout = useRef(null)

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setConnected(true)
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setConnected(false)
        // Reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(connect, 3000)
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          setData(message)
        } catch (e) {
          console.error('Failed to parse message:', e)
        }
      }
    } catch (error) {
      console.error('Failed to connect:', error)
    }
  }, [url])

  const send = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    }
  }, [])

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current)
    }
    if (ws.current) {
      ws.current.close()
    }
  }, [])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return { connected, data, send, disconnect }
}

export default useWebSocket
