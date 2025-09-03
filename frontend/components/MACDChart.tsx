'use client';

import React, { useEffect, useRef, memo } from 'react';
import { createChart, ColorType, LineStyle } from 'lightweight-charts';
import { useTheme } from 'next-themes';
import { CandlestickData } from './CandlestickChart'; // Reuse the main data type

interface MACDChartProps {
  data: CandlestickData[];
  height?: number;
}

const MACDChart = ({ data, height = 150 }: MACDChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
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
      macdLineColor: '#2962FF',
      signalLineColor: '#FF6D00',
      histPositiveColor: 'rgba(38, 166, 154, 0.4)',
      histNegativeColor: 'rgba(239, 83, 80, 0.4)',
    };

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: chartColors.background },
        textColor: chartColors.textColor,
      },
      width: chartContainerRef.current.clientWidth,
      height: height,
      grid: {
        vertLines: { color: chartColors.gridColor, style: LineStyle.Dashed },
        horzLines: { color: chartColors.gridColor, style: LineStyle.Dashed },
      },
      timeScale: { visible: false }, // Hide time scale as it will be synced with the main chart
      rightPriceScale: { borderColor: chartColors.gridColor, scaleMargins: { top: 0.2, bottom: 0.2 } },
      crosshair: { mode: 1 },
    });

    // MACD Histogram
    const macdHistogramSeries = chart.addHistogramSeries({
        priceFormat: { type: 'volume' },
        lastValueVisible: false,
        priceLineVisible: false,
    });
    const histogramData = data
        .filter(d => d.MACD_histogram != null)
        .map(d => ({ 
            time: d.time, 
            value: d.MACD_histogram!,
            color: d.MACD_histogram! >= 0 ? chartColors.histPositiveColor : chartColors.histNegativeColor,
        }));
    macdHistogramSeries.setData(histogramData);

    // MACD Line
    const macdLineSeries = chart.addLineSeries({ 
      color: chartColors.macdLineColor,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      title: 'MACD'
    });
    macdLineSeries.setData(data.filter(d => d.MACD_line != null).map(d => ({ time: d.time, value: d.MACD_line! })));

    // Signal Line
    const signalLineSeries = chart.addLineSeries({ 
      color: chartColors.signalLineColor, 
      lineWidth: 2, 
      priceLineVisible: false,
      lastValueVisible: false,
      title: 'Signal'
    });
    signalLineSeries.setData(data.filter(d => d.Signal_line != null).map(d => ({ time: d.time, value: d.Signal_line! })));


    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, theme, height]);

  return <div ref={chartContainerRef} className="w-full" style={{ height: `${height}px` }}/>;
};

export default memo(MACDChart);
