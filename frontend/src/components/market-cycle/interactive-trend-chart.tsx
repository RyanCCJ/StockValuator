"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import {
    createChart,
    IChartApi,
    ISeriesApi,
    CandlestickSeries,
    LineSeries,
    CrosshairMode,
    Time,
    MouseEventParams,
    ColorType,
} from "lightweight-charts";
import { OHLCDataPoint, LineDataPoint } from "@/services/api";

interface InteractiveTrendChartProps {
    title: string;
    chartType: "candlestick" | "line";
    ohlcData?: OHLCDataPoint[] | null;
    lineData?: LineDataPoint[] | null;
    color?: string;
    height?: number;
    showMA?: boolean;  // Show MA20, MA50, MA200
    showVIXLevels?: boolean;  // Show 15 (greed) and 30 (fear) reference lines
}

interface TooltipData {
    visible: boolean;
    x: number;
    y: number;
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    change: number;
    changePercent: number;
    ma20?: number;
    ma50?: number;
    ma200?: number;
}

// Calculate Moving Average from OHLC data
function calculateMA(ohlcData: OHLCDataPoint[], period: number): { time: string; value: number }[] {
    const maData: { time: string; value: number }[] = [];
    const closes = ohlcData.map(d => d.close);

    for (let i = period - 1; i < closes.length; i++) {
        const sum = closes.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        maData.push({
            time: ohlcData[i].time,
            value: sum / period,
        });
    }

    return maData;
}

// MA Colors
const MA_COLORS = {
    ma20: "#22c55e",   // green
    ma50: "#f59e0b",   // amber
    ma200: "#3b82f6",  // blue
};

export function InteractiveTrendChart({
    title,
    chartType,
    ohlcData,
    lineData,
    color = "#2962FF",
    height = 200,
    showMA = false,
    showVIXLevels = false,
}: InteractiveTrendChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<ISeriesApi<"Candlestick"> | ISeriesApi<"Line"> | null>(null);
    const ma20SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
    const ma50SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
    const ma200SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
    const vixLevelsAddedRef = useRef(false);
    const [tooltipData, setTooltipData] = useState<TooltipData | null>(null);
    const initializedRef = useRef(false);

    // Detect dark mode
    const [isDark, setIsDark] = useState(true);
    useEffect(() => {
        const checkDark = () => setIsDark(document.documentElement.classList.contains('dark'));
        checkDark();
        const observer = new MutationObserver(checkDark);
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
        return () => observer.disconnect();
    }, []);

    // Theme-aware colors
    const gridColor = isDark ? "#1f2937" : "#e5e7eb";
    const borderColor = isDark ? "#374151" : "#d1d5db";
    const textColor = isDark ? "#9ca3af" : "#6b7280";

    // Calculate MA data with useMemo to avoid recalculation
    const ma20Data = useMemo(() =>
        showMA && ohlcData && ohlcData.length >= 20 ? calculateMA(ohlcData, 20) : null,
        [showMA, ohlcData]
    );
    const ma50Data = useMemo(() =>
        showMA && ohlcData && ohlcData.length >= 50 ? calculateMA(ohlcData, 50) : null,
        [showMA, ohlcData]
    );
    const ma200Data = useMemo(() =>
        showMA && ohlcData && ohlcData.length >= 200 ? calculateMA(ohlcData, 200) : null,
        [showMA, ohlcData]
    );

    // Create MA lookups for tooltip
    const ma20Lookup = useMemo(() =>
        ma20Data ? Object.fromEntries(ma20Data.map(d => [d.time, d.value])) : {},
        [ma20Data]
    );
    const ma50Lookup = useMemo(() =>
        ma50Data ? Object.fromEntries(ma50Data.map(d => [d.time, d.value])) : {},
        [ma50Data]
    );
    const ma200Lookup = useMemo(() =>
        ma200Data ? Object.fromEntries(ma200Data.map(d => [d.time, d.value])) : {},
        [ma200Data]
    );

    // Initialize chart and series (only once)
    useEffect(() => {
        if (!chartContainerRef.current || initializedRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: "transparent" },
                textColor: textColor,
            },
            grid: {
                vertLines: { color: gridColor },
                horzLines: { color: gridColor },
            },
            crosshair: {
                mode: CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: borderColor,
            },
            timeScale: {
                borderColor: borderColor,
                timeVisible: true,
                secondsVisible: false,
            },
            handleScale: true,
            handleScroll: true,
        });

        chartRef.current = chart;

        // Create main series
        if (chartType === "candlestick") {
            const candlestickSeries = chart.addSeries(CandlestickSeries, {
                upColor: "#22c55e",
                downColor: "#ef4444",
                borderUpColor: "#22c55e",
                borderDownColor: "#ef4444",
                wickUpColor: "#22c55e",
                wickDownColor: "#ef4444",
            });
            seriesRef.current = candlestickSeries;
        } else {
            const lineSeries = chart.addSeries(LineSeries, {
                color: color,
                lineWidth: 2,
            });
            seriesRef.current = lineSeries;
        }

        // Create MA series if enabled (only once)
        if (showMA) {
            ma20SeriesRef.current = chart.addSeries(LineSeries, {
                color: MA_COLORS.ma20,
                lineWidth: 1,
                priceLineVisible: false,
                title: "MA20",
            });

            ma50SeriesRef.current = chart.addSeries(LineSeries, {
                color: MA_COLORS.ma50,
                lineWidth: 1,
                priceLineVisible: false,
                title: "MA50",
            });

            ma200SeriesRef.current = chart.addSeries(LineSeries, {
                color: MA_COLORS.ma200,
                lineWidth: 1,
                priceLineVisible: false,
                title: "MA200",
            });
        }

        // Handle resize
        const resizeObserver = new ResizeObserver((entries) => {
            const { width } = entries[0].contentRect;
            chart.applyOptions({ width });
            chart.timeScale().fitContent();
        });

        resizeObserver.observe(chartContainerRef.current);
        initializedRef.current = true;

        return () => {
            resizeObserver.disconnect();
            chart.remove();
            chartRef.current = null;
            seriesRef.current = null;
            ma20SeriesRef.current = null;
            ma50SeriesRef.current = null;
            ma200SeriesRef.current = null;
            vixLevelsAddedRef.current = false;
            initializedRef.current = false;
        };
    }, [chartType, color, showMA, gridColor, borderColor, textColor]);

    // Update data (separate from initialization)
    useEffect(() => {
        if (!chartRef.current || !seriesRef.current) return;

        if (chartType === "candlestick" && ohlcData && ohlcData.length > 0) {
            const formattedData = ohlcData.map((d) => ({
                time: d.time as Time,
                open: d.open,
                high: d.high,
                low: d.low,
                close: d.close,
            }));
            (seriesRef.current as ISeriesApi<"Candlestick">).setData(formattedData);

            // Update MA data
            if (showMA) {
                if (ma20SeriesRef.current && ma20Data) {
                    ma20SeriesRef.current.setData(ma20Data.map(d => ({
                        time: d.time as Time,
                        value: d.value,
                    })));
                }
                if (ma50SeriesRef.current && ma50Data) {
                    ma50SeriesRef.current.setData(ma50Data.map(d => ({
                        time: d.time as Time,
                        value: d.value,
                    })));
                }
                if (ma200SeriesRef.current && ma200Data) {
                    ma200SeriesRef.current.setData(ma200Data.map(d => ({
                        time: d.time as Time,
                        value: d.value,
                    })));
                }
            }

            // Add VIX reference lines (only once)
            if (showVIXLevels && !vixLevelsAddedRef.current) {
                const series = seriesRef.current as ISeriesApi<"Candlestick">;
                series.createPriceLine({
                    price: 15,
                    color: "#f59e0b",
                    lineWidth: 1,
                    lineStyle: 2,
                    axisLabelVisible: true,
                    title: "Greed",
                });
                series.createPriceLine({
                    price: 30,
                    color: "#ef4444",
                    lineWidth: 1,
                    lineStyle: 2,
                    axisLabelVisible: true,
                    title: "Fear",
                });
                vixLevelsAddedRef.current = true;
            }

            chartRef.current.timeScale().fitContent();
        } else if (chartType === "line" && lineData && lineData.length > 0) {
            const formattedData = lineData.map((d) => ({
                time: d.time as Time,
                value: d.value,
            }));
            (seriesRef.current as ISeriesApi<"Line">).setData(formattedData);
            chartRef.current.timeScale().fitContent();
        }
    }, [chartType, ohlcData, lineData, showMA, showVIXLevels, ma20Data, ma50Data, ma200Data]);

    // Handle crosshair move for tooltip
    useEffect(() => {
        if (!chartRef.current || !ohlcData || ohlcData.length === 0) return;

        const handleCrosshairMove = (param: MouseEventParams<Time>) => {
            if (!param.time || !param.point || param.point.x < 0 || param.point.y < 0) {
                setTooltipData(null);
                return;
            }

            const dateStr = param.time as string;
            const ohlcIndex = ohlcData.findIndex(d => d.time === dateStr);

            if (ohlcIndex >= 0) {
                const candle = ohlcData[ohlcIndex];
                const prevClose = ohlcIndex > 0 ? ohlcData[ohlcIndex - 1].close : candle.open;
                const change = candle.close - prevClose;
                const changePercent = (change / prevClose) * 100;

                setTooltipData({
                    visible: true,
                    x: param.point.x,
                    y: param.point.y,
                    date: dateStr,
                    open: candle.open,
                    high: candle.high,
                    low: candle.low,
                    close: candle.close,
                    change,
                    changePercent,
                    ma20: ma20Lookup[dateStr],
                    ma50: ma50Lookup[dateStr],
                    ma200: ma200Lookup[dateStr],
                });
            }
        };

        chartRef.current.subscribeCrosshairMove(handleCrosshairMove);

        return () => {
            chartRef.current?.unsubscribeCrosshairMove(handleCrosshairMove);
        };
    }, [ohlcData, ma20Lookup, ma50Lookup, ma200Lookup]);

    const hasData = (chartType === "candlestick" && ohlcData && ohlcData.length > 0) ||
        (chartType === "line" && lineData && lineData.length > 0);

    return (
        <div className="flex flex-col h-full relative">
            {/* Header with title */}
            <div className="flex items-center justify-between mb-2 min-h-[24px]">
                <span className="text-sm font-medium">{title}</span>
            </div>

            {/* Chart container */}
            <div
                ref={chartContainerRef}
                style={{ height: `${height}px` }}
                className="w-full"
            />

            {/* Floating tooltip */}
            {tooltipData && chartContainerRef.current && (
                <div
                    className="absolute pointer-events-none z-50 px-3 py-2 rounded-md shadow-lg text-sm
                               bg-background/90 dark:bg-card/90 border border-border backdrop-blur-sm"
                    style={{
                        left: Math.min(tooltipData.x + 15, (chartContainerRef.current?.clientWidth || 300) - 160),
                        top: Math.max(tooltipData.y - 30, 30),
                    }}
                >
                    <div className="font-medium text-foreground mb-1">{tooltipData.date}</div>
                    <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-xs">
                        <span className="text-muted-foreground">Open</span>
                        <span className="text-foreground text-right">{tooltipData.open.toFixed(2)}</span>
                        <span className="text-muted-foreground">High</span>
                        <span className="text-foreground text-right">{tooltipData.high.toFixed(2)}</span>
                        <span className="text-muted-foreground">Low</span>
                        <span className="text-foreground text-right">{tooltipData.low.toFixed(2)}</span>
                        <span className="text-muted-foreground">Close</span>
                        <span className="text-foreground text-right">{tooltipData.close.toFixed(2)}</span>
                    </div>
                    <div className={`text-xs mt-1 font-medium ${tooltipData.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {tooltipData.change >= 0 ? '+' : ''}{tooltipData.change.toFixed(2)} ({tooltipData.changePercent >= 0 ? '+' : ''}{tooltipData.changePercent.toFixed(2)}%)
                    </div>
                </div>
            )}

            {/* No data message */}
            {!hasData && (
                <div className="absolute inset-0 flex items-center justify-center text-muted-foreground text-sm">
                    No data available
                </div>
            )}
        </div>
    );
}
