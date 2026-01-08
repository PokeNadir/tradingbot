import { useEffect, useRef, memo } from 'react'
import { createChart, ColorType, CrosshairMode } from 'lightweight-charts'

function PriceChart({ data, symbol, indicators }) {
  const chartContainerRef = useRef()
  const chartRef = useRef()
  const candlestickSeriesRef = useRef()
  const volumeSeriesRef = useRef()
  const ema9Ref = useRef()
  const ema21Ref = useRef()
  const bbUpperRef = useRef()
  const bbLowerRef = useRef()

  useEffect(() => {
    if (!chartContainerRef.current) return

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0d1117' },
        textColor: '#8b949e',
      },
      grid: {
        vertLines: { color: '#21262d' },
        horzLines: { color: '#21262d' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: '#21262d',
      },
      timeScale: {
        borderColor: '#21262d',
        timeVisible: true,
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
    })

    chartRef.current = chart

    // Candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderDownColor: '#ef4444',
      borderUpColor: '#22c55e',
      wickDownColor: '#ef4444',
      wickUpColor: '#22c55e',
    })
    candlestickSeriesRef.current = candlestickSeries

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#3b82f6',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.85,
        bottom: 0,
      },
    })
    volumeSeriesRef.current = volumeSeries

    // EMA 9 (fast)
    const ema9 = chart.addLineSeries({
      color: '#eab308',
      lineWidth: 1,
      title: 'EMA 9',
    })
    ema9Ref.current = ema9

    // EMA 21 (slow)
    const ema21 = chart.addLineSeries({
      color: '#f97316',
      lineWidth: 1,
      title: 'EMA 21',
    })
    ema21Ref.current = ema21

    // Bollinger Bands
    const bbUpper = chart.addLineSeries({
      color: '#8b5cf6',
      lineWidth: 1,
      lineStyle: 2,
      title: 'BB Upper',
    })
    bbUpperRef.current = bbUpper

    const bbLower = chart.addLineSeries({
      color: '#8b5cf6',
      lineWidth: 1,
      lineStyle: 2,
      title: 'BB Lower',
    })
    bbLowerRef.current = bbLower

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [])

  // Update data when it changes
  useEffect(() => {
    if (!data || data.length === 0) return
    if (!candlestickSeriesRef.current) return

    // Format data for lightweight-charts
    const candleData = data.map(d => ({
      time: new Date(d.timestamp).getTime() / 1000,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }))

    const volumeData = data.map(d => ({
      time: new Date(d.timestamp).getTime() / 1000,
      value: d.volume,
      color: d.close >= d.open ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)',
    }))

    candlestickSeriesRef.current.setData(candleData)
    volumeSeriesRef.current.setData(volumeData)

    // Update indicators if available
    if (indicators) {
      // EMA 9
      if (data.some(d => d.ema_9)) {
        const ema9Data = data
          .filter(d => d.ema_9 != null)
          .map(d => ({
            time: new Date(d.timestamp).getTime() / 1000,
            value: d.ema_9,
          }))
        ema9Ref.current?.setData(ema9Data)
      }

      // EMA 21
      if (data.some(d => d.ema_21)) {
        const ema21Data = data
          .filter(d => d.ema_21 != null)
          .map(d => ({
            time: new Date(d.timestamp).getTime() / 1000,
            value: d.ema_21,
          }))
        ema21Ref.current?.setData(ema21Data)
      }

      // Bollinger Bands
      if (data.some(d => d.bb_upper)) {
        const bbUpperData = data
          .filter(d => d.bb_upper != null)
          .map(d => ({
            time: new Date(d.timestamp).getTime() / 1000,
            value: d.bb_upper,
          }))
        bbUpperRef.current?.setData(bbUpperData)

        const bbLowerData = data
          .filter(d => d.bb_lower != null)
          .map(d => ({
            time: new Date(d.timestamp).getTime() / 1000,
            value: d.bb_lower,
          }))
        bbLowerRef.current?.setData(bbLowerData)
      }
    }

    // Fit content
    chartRef.current?.timeScale().fitContent()
  }, [data, indicators])

  return (
    <div ref={chartContainerRef} className="w-full h-full" />
  )
}

export default memo(PriceChart)
