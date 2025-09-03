'use client';

import React, { useState, useEffect, useRef, memo } from 'react';
import { createChart, ColorType, LineStyle } from 'lightweight-charts';
import { useTheme } from 'next-themes';
import { cn } from "@/lib/utils";

export interface CandlestickData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  Volume?: number | null;
  UpperBand?: number | null;
  MiddleBand?: number | null;
  LowerBand?: number | null;
  MA7?: number | null;
  MA30?: number | null;
  MA90?: number | null;
  EMA5?: number | null;
  EMA10?: number | null;
  EMA20?: number | null;
  MACD_line?: number | null;
  Signal_line?: number | null;
  MACD_histogram?: number | null;
}

interface ChartProps {
  data: CandlestickData[];
  ticker: string;
  showBands: boolean;
  showMA: boolean;
  showEMA: boolean;
  showLevels: boolean;
  levels: { [key: string]: number } | null
}

const CandlestickChart = ({ data, ticker, showBands, showMA, showEMA, levels, showLevels }: ChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{ top: number; left: number; visible: boolean; content: CandlestickData | null }>({ top: 0, left: 0, visible: false, content: null });
  const { theme } = useTheme();

  useEffect(() => {
    if (!chartContainerRef.current || data.length === 0) return;

    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current!.clientWidth });
    };

    const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    const chartColors = {
      background: isDark ? '#020817' : '#FFFFFF',
      textColor: isDark ? '#D1D5DB' : '#333333',
      gridColor: isDark ? '#2A2E39' : '#E5E7EB',
      upColor: isDark ? '#26A69A' : '#22C55E',
      downColor: isDark ? '#EF5350' : '#EF4444',
      bbColor: isDark ? 'rgba(147, 197, 253, 0.7)' : 'rgba(59, 130, 246, 0.7)',
      ma7Color: '#F43F5E',
      ma30Color: '#3B82F6',
      ma90Color: '#A855F7',
      ema5Color: '#F97316',
      ema10Color: '#84CC16',
      ema20Color: '#06B6D4',
      supportColor: '#22c55e',
      resistanceColor: '#ef4444',
    };

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: chartColors.background },
        textColor: chartColors.textColor,
      },
      width: chartContainerRef.current.clientWidth,
      height: 450,
      grid: {
        vertLines: { color: chartColors.gridColor, style: LineStyle.Dashed },
        horzLines: { color: chartColors.gridColor, style: LineStyle.Dashed },
      },
      timeScale: { timeVisible: true, secondsVisible: false, borderColor: chartColors.gridColor },
      rightPriceScale: { borderColor: chartColors.gridColor },
      crosshair: { 
        mode: 1,
        vertLine: { labelVisible: false },
        horzLine: { labelVisible: false },
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
      upColor: chartColors.upColor, downColor: chartColors.downColor,
      borderDownColor: chartColors.downColor, borderUpColor: chartColors.upColor,
      wickDownColor: chartColors.downColor, wickUpColor: chartColors.upColor,
    });
    candlestickSeries.setData(data);

    if (showLevels && levels) {
      Object.entries(levels).forEach(([key, price]) => {
        if (price) {
          candlestickSeries.createPriceLine({
            price: price,
            color: key.startsWith('s') ? chartColors.supportColor : chartColors.resistanceColor,
            lineWidth: 1,
            title: key.toUpperCase(),
          });
        }
      });
    }

    if (showBands) {
      const bbUpperSeries = chart.addLineSeries({ 
        color: chartColors.bbColor,
        lineWidth: 1,
        priceLineVisible: false,
        title: 'BB Upper'
      });
      const bbMiddleSeries = chart.addLineSeries({ 
        color: chartColors.bbColor,
        lineWidth: 1,
        priceLineVisible: false,
        title: 'BB Middle'
      });
      const bbLowerSeries = chart.addLineSeries({ 
        color: chartColors.bbColor,
        lineWidth: 1,
        priceLineVisible: false,
        title: 'BB Lower'
      });
      bbUpperSeries.setData(data.filter(d => d.UpperBand != null).map(d => ({ time: d.time, value: d.UpperBand! })));
      bbMiddleSeries.setData(data.filter(d => d.MiddleBand != null).map(d => ({ time: d.time, value: d.MiddleBand! })));
      bbLowerSeries.setData(data.filter(d => d.LowerBand != null).map(d => ({ time: d.time, value: d.LowerBand! })));
    }

    if (showMA) {
      const bbUpperSeries = chart.addLineSeries({ 
        color: chartColors.bbColor, 
        lineWidth: 1,  
        priceLineVisible: false,  
        title: 'BB Upper' 
      });
      const ma7 = chart.addLineSeries({ 
        color: chartColors.ma7Color,
        lineWidth: 1,
        priceLineVisible: false,
        title: 'MA 7' 
      });
      const ma30 = chart.addLineSeries({ 
        color: chartColors.ma30Color,
        lineWidth: 1,
        priceLineVisible: false,
        title: 'MA 30' 
      });
      const ma90 = chart.addLineSeries({ 
        color: chartColors.ma90Color,
        lineWidth: 1,
        priceLineVisible: false,
        title: 'MA 90' 
      });
      ma7.setData(data.filter(d => d.MA7 != null).map(d => ({ time: d.time, value: d.MA7! })));
      ma30.setData(data.filter(d => d.MA30 != null).map(d => ({ time: d.time, value: d.MA30! })));
      ma90.setData(data.filter(d => d.MA90 != null).map(d => ({ time: d.time, value: d.MA90! })));
    }

    if (showEMA) {
      const ema5 = chart.addLineSeries({ 
        color: chartColors.ema5Color,
        lineWidth: 1,
        priceLineVisible: false,
        title: 'EMA 5'
      });
      const ema10 = chart.addLineSeries({ 
        color: chartColors.ema10Color,
        lineWidth: 1,
        priceLineVisible: false,
        title: 'EMA 10'
      });
      const ema20 = chart.addLineSeries({ 
        color: chartColors.ema20Color,
        lineWidth: 1,
        priceLineVisible: false,
        title: 'EMA 20'
      });
      ema5.setData(data.filter(d => d.EMA5 != null).map(d => ({ time: d.time, value: d.EMA5! })));
      ema10.setData(data.filter(d => d.EMA10 != null).map(d => ({ time: d.time, value: d.EMA10! })));
      ema20.setData(data.filter(d => d.EMA20 != null).map(d => ({ time: d.time, value: d.EMA20! })));
    }

    chart.subscribeCrosshairMove(param => {
      if (!param.time || !param.point || !candlestickSeries) {
        setTooltip(prev => ({ ...prev, visible: false }));
        return;
      }
      const dataPoint = data.find(d => d.time === param.time);
      if (!dataPoint) {
        setTooltip(prev => ({ ...prev, visible: false }));
        return;
      }
      let left = param.point.x + 20;
      if (chartContainerRef.current && left > chartContainerRef.current.clientWidth - 150) {
        left = param.point.x - 170;
      }
      setTooltip({ top: param.point.y, left, visible: true, content: dataPoint });
    });

    chart.timeScale().fitContent();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, ticker, theme, showBands, showMA, showEMA, levels, showLevels]);

  const change = tooltip.content ? tooltip.content.close - tooltip.content.open : 0;
  const percentChange = tooltip.content ? (change / tooltip.content.open) * 100 : 0;
  const changeColor = change >= 0 ? 'text-green-500' : 'text-red-500';

  return (
    <div ref={chartContainerRef} className="w-full relative" style={{ height: '450px' }}>
      {tooltip.visible && tooltip.content && (
        <div
          className="absolute z-10 p-2 text-sm rounded-md shadow-md pointer-events-none bg-background/75 border border-border text-foreground"
          style={{ top: tooltip.top, left: tooltip.left }}
        >
          <div className="font-bold mb-1">{new Date(tooltip.content.time).toLocaleDateString()}</div>
          <div className="grid grid-cols-[auto_1fr] gap-x-2">
            <span>Open:</span><span className="font-bold text-right">{tooltip.content.open.toFixed(2)}</span>
            <span>High:</span><span className="font-bold text-right">{tooltip.content.high.toFixed(2)}</span>
            <span>Low:</span><span className="font-bold text-right">{tooltip.content.low.toFixed(2)}</span>
            <span>Close:</span><span className="font-bold text-right">{tooltip.content.close.toFixed(2)}</span>
            <span className={changeColor}>Change:</span><span className={cn("font-bold text-right", changeColor)}>{change.toFixed(2)} ({percentChange.toFixed(2)}%)</span>
            <span>Volume:</span><span className="font-bold text-right">{(tooltip.content.Volume || 0).toLocaleString()}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default memo(CandlestickChart);