import { useEffect, useRef, memo, useCallback } from 'react'
import { createChart, ColorType, CrosshairMode } from 'lightweight-charts'

function PriceChart({ data, symbol, timeframe, indicators }) {
  const chartContainerRef = useRef()
  const chartRef = useRef()
  const candlestickSeriesRef = useRef()
  const volumeSeriesRef = useRef()
  const ema9Ref = useRef()
  const ema21Ref = useRef()
  const bbUpperRef = useRef()
  const bbLowerRef = useRef()

  // Calculate appropriate price precision based on the asset price
  const getPriceFormat = useCallback((price) => {
    if (!price || price === 0) return { precision: 2, minMove: 0.01 }
    if (price < 0.0001) return { precision: 8, minMove: 0.00000001 }
    if (price < 0.001) return { precision: 7, minMove: 0.0000001 }
    if (price < 0.01) return { precision: 6, minMove: 0.000001 }
    if (price < 0.1) return { precision: 5, minMove: 0.00001 }
    if (price < 1) return { precision: 4, minMove: 0.0001 }
    if (price < 10) return { precision: 3, minMove: 0.001 }
    if (price < 1000) return { precision: 2, minMove: 0.01 }
    return { precision: 2, minMove: 0.01 }
  }, [])

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
        vertLine: {
          width: 1,
          color: '#505050',
          style: 3,
        },
        horzLine: {
          width: 1,
          color: '#505050',
          style: 3,
        },
      },
      rightPriceScale: {
        borderColor: '#21262d',
        autoScale: true,
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: '#21262d',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 5,
        barSpacing: 10,
        minBarSpacing: 5,
        fixLeftEdge: true,
        fixRightEdge: true,
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      handleScroll: {
        vertTouchDrag: false,
      },
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
      crosshairMarkerVisible: false,
    })
    ema9Ref.current = ema9

    // EMA 21 (slow)
    const ema21 = chart.addLineSeries({
      color: '#f97316',
      lineWidth: 1,
      title: 'EMA 21',
      crosshairMarkerVisible: false,
    })
    ema21Ref.current = ema21

    // Bollinger Bands
    const bbUpper = chart.addLineSeries({
      color: '#8b5cf6',
      lineWidth: 1,
      lineStyle: 2,
      title: 'BB Upper',
      crosshairMarkerVisible: false,
    })
    bbUpperRef.current = bbUpper

    const bbLower = chart.addLineSeries({
      color: '#8b5cf6',
      lineWidth: 1,
      lineStyle: 2,
      title: 'BB Lower',
      crosshairMarkerVisible: false,
    })
    bbLowerRef.current = bbLower

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    // Also observe container size changes
    const resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(chartContainerRef.current)

    return () => {
      window.removeEventListener('resize', handleResize)
      resizeObserver.disconnect()
      chart.remove()
    }
  }, [])

  // Update data when it changes
  useEffect(() => {
    if (!data || data.length === 0) return
    if (!candlestickSeriesRef.current || !chartRef.current) return

    // Get a sample price to determine precision
    const samplePrice = data[data.length - 1]?.close || 0
    const priceFormat = getPriceFormat(samplePrice)

    // Update candlestick series price format
    candlestickSeriesRef.current.applyOptions({
      priceFormat: {
        type: 'price',
        precision: priceFormat.precision,
        minMove: priceFormat.minMove,
      },
    })

    // Update all line series price formats
    const lineSeries = [ema9Ref.current, ema21Ref.current, bbUpperRef.current, bbLowerRef.current]
    lineSeries.forEach(series => {
      if (series) {
        series.applyOptions({
          priceFormat: {
            type: 'price',
            precision: priceFormat.precision,
            minMove: priceFormat.minMove,
          },
        })
      }
    })

    // Format data for lightweight-charts
    const candleData = data.map(d => ({
      time: new Date(d.timestamp).getTime() / 1000,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    })).sort((a, b) => a.time - b.time)

    const volumeData = data.map(d => ({
      time: new Date(d.timestamp).getTime() / 1000,
      value: d.volume,
      color: d.close >= d.open ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)',
    })).sort((a, b) => a.time - b.time)

    candlestickSeriesRef.current.setData(candleData)
    volumeSeriesRef.current.setData(volumeData)

    // Clear indicator data first
    ema9Ref.current?.setData([])
    ema21Ref.current?.setData([])
    bbUpperRef.current?.setData([])
    bbLowerRef.current?.setData([])

    // Update indicators if available in data
    if (data.some(d => d.ema_9 != null)) {
      const ema9Data = data
        .filter(d => d.ema_9 != null)
        .map(d => ({
          time: new Date(d.timestamp).getTime() / 1000,
          value: d.ema_9,
        }))
        .sort((a, b) => a.time - b.time)
      ema9Ref.current?.setData(ema9Data)
    }

    if (data.some(d => d.ema_21 != null)) {
      const ema21Data = data
        .filter(d => d.ema_21 != null)
        .map(d => ({
          time: new Date(d.timestamp).getTime() / 1000,
          value: d.ema_21,
        }))
        .sort((a, b) => a.time - b.time)
      ema21Ref.current?.setData(ema21Data)
    }

    if (data.some(d => d.bb_upper != null)) {
      const bbUpperData = data
        .filter(d => d.bb_upper != null)
        .map(d => ({
          time: new Date(d.timestamp).getTime() / 1000,
          value: d.bb_upper,
        }))
        .sort((a, b) => a.time - b.time)
      bbUpperRef.current?.setData(bbUpperData)

      const bbLowerData = data
        .filter(d => d.bb_lower != null)
        .map(d => ({
          time: new Date(d.timestamp).getTime() / 1000,
          value: d.bb_lower,
        }))
        .sort((a, b) => a.time - b.time)
      bbLowerRef.current?.setData(bbLowerData)
    }

    // Auto-fit content with visible range
    chartRef.current.timeScale().fitContent()

    // Optionally show only last N candles based on timeframe
    const visibleBars = getVisibleBars(timeframe)
    if (candleData.length > visibleBars) {
      const from = candleData[candleData.length - visibleBars].time
      const to = candleData[candleData.length - 1].time
      chartRef.current.timeScale().setVisibleRange({ from, to })
    }
  }, [data, timeframe, getPriceFormat])

  // Determine how many bars to show based on timeframe
  const getVisibleBars = (tf) => {
    switch (tf) {
      case '1m': return 120
      case '5m': return 100
      case '15m': return 80
      case '30m': return 60
      case '1h': return 50
      case '4h': return 50
      case '1d': return 60
      default: return 80
    }
  }

  return (
    <div ref={chartContainerRef} className="w-full h-full" />
  )
}

export default memo(PriceChart)
