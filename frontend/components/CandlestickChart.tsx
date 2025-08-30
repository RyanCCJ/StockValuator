'use client';

import React, { useEffect, useRef, memo } from 'react';
import { createChart, ColorType, LineStyle } from 'lightweight-charts';
import { useTheme } from 'next-themes';

export interface CandlestickData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

const CandlestickChart = ({ data, ticker }: { data: CandlestickData[], ticker: string }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();

  useEffect(() => {
    if (!chartContainerRef.current || data.length === 0) return;

    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current!.clientWidth });
    };

    // Determine theme based on next-themes and system preference
    const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    const chartColors = {
      background: isDark ? '#020817' : '#FFFFFF',
      textColor: isDark ? '#D1D5DB' : '#333333',
      gridColor: isDark ? '#2A2E39' : '#E5E7EB',
      upColor: isDark ? '#26a69a' : '#22c55e',
      downColor: isDark ? '#ef5350' : '#ef4444',
    };

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: chartColors.background },
        textColor: chartColors.textColor,
      },
      width: chartContainerRef.current.clientWidth,
      height: 450,
      grid: {
        vertLines: {
          color: chartColors.gridColor,
          style: LineStyle.Dashed,
        },
        horzLines: {
          color: chartColors.gridColor,
          style: LineStyle.Dashed,
        },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: chartColors.gridColor,
      },
      rightPriceScale: {
        borderColor: chartColors.gridColor,
      },
      crosshair: {
        mode: 1, // Magnet mode
      },
      watermark: {
        color: 'rgba(150, 150, 150, 0.2)',
        visible: true,
        text: ticker,
        fontSize: 48,
        horzAlign: 'center',
        vertAlign: 'center',
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: chartColors.upColor,
      downColor: chartColors.downColor,
      borderDownColor: chartColors.downColor,
      borderUpColor: chartColors.upColor,
      wickDownColor: chartColors.downColor,
      wickUpColor: chartColors.upColor,
    });

    candlestickSeries.setData(data);
    chart.timeScale().fitContent();

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, ticker, theme]); // Rerun effect if theme changes

  return <div ref={chartContainerRef} className="w-full" style={{ height: '450px' }}/>;
};

export default memo(CandlestickChart);
