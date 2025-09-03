'use client';

import React, { useEffect, useRef, memo } from 'react';
import { createChart, ColorType, LineStyle } from 'lightweight-charts';
import { useTheme } from 'next-themes';
import { CandlestickData } from './CandlestickChart'; // Reuse the main data type

interface VolumeChartProps {
  data: CandlestickData[];
  height?: number;
}

const VolumeChart = ({ data, height = 150 }: VolumeChartProps) => {
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
      upColor: 'rgba(38, 166, 154, 0.5)', // Semi-transparent green
      downColor: 'rgba(239, 83, 80, 0.5)', // Semi-transparent red
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
      timeScale: { visible: false },
      rightPriceScale: { 
        borderColor: chartColors.gridColor,
      },
      crosshair: { mode: 1 },
    });

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume'},
      lastValueVisible: false,
      priceLineVisible: false,
      title: 'Volume'
    });
    volumeSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.2, bottom: 0 },
    });

    const volumeData = data.map(d => ({
      time: d.time,
      value: d.Volume, // Assuming Volume is passed in CandlestickData
      color: d.close >= d.open ? chartColors.upColor : chartColors.downColor,
    }));

    volumeSeries.setData(volumeData);

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, theme, height]);

  return <div ref={chartContainerRef} className="w-full" style={{ height: `${height}px` }}/>;
};

export default memo(VolumeChart);
