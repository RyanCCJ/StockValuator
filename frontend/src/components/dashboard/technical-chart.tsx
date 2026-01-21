"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import {
    createChart,
    IChartApi,
    CandlestickData,
    LineData,
    HistogramData,
    ColorType,
    Time,
    CandlestickSeries,
    LineSeries,
    HistogramSeries,
} from "lightweight-charts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TechnicalDataResponse, OHLCVData } from "@/services/api";

// Export types for external use
export interface IndicatorVisibility {
    ma: boolean;
    bollinger: boolean;
    volume: boolean;
    rsi: boolean;
    macd: boolean;
    stochastic: boolean;
}

export const DEFAULT_VISIBILITY: IndicatorVisibility = {
    ma: false,
    bollinger: false,
    volume: false,
    rsi: false,
    macd: false,
    stochastic: false,
};

export const STORAGE_KEY_INDICATORS = "technicalChartIndicators";
export const STORAGE_KEY_PERIOD = "technicalChartPeriod";

// Hook for managing indicator visibility with localStorage
export function useIndicatorVisibility() {
    const [visibility, setVisibility] = useState<IndicatorVisibility>(() => {
        if (typeof window !== "undefined") {
            const saved = localStorage.getItem(STORAGE_KEY_INDICATORS);
            if (saved) {
                try {
                    return { ...DEFAULT_VISIBILITY, ...JSON.parse(saved) };
                } catch {
                    return DEFAULT_VISIBILITY;
                }
            }
        }
        return DEFAULT_VISIBILITY;
    });

    useEffect(() => {
        if (typeof window !== "undefined") {
            localStorage.setItem(STORAGE_KEY_INDICATORS, JSON.stringify(visibility));
        }
    }, [visibility]);

    const toggleIndicator = (key: keyof IndicatorVisibility) => {
        setVisibility((prev) => ({ ...prev, [key]: !prev[key] }));
    };

    return { visibility, toggleIndicator };
}

interface TechnicalChartProps {
    data: TechnicalDataResponse;
    visibility: IndicatorVisibility;
}

const INDICATOR_COLORS = {
    ma5: "#22c55e",
    ma20: "#f59e0b",
    ma60: "#3b82f6",
    bollingerUpper: "#6366f1",
    bollingerLower: "#6366f1",
    bollingerMiddle: "#a5b4fc",
    volume: "#64748b",
    rsi: "#22c55e",
    macdLine: "#3b82f6",
    macdSignal: "#f59e0b",
    macdHistPos: "#22c55e80",  // green with transparency
    macdHistNeg: "#ef444480",  // red with transparency
    stochasticK: "#3b82f6",
    stochasticD: "#f59e0b",
    stochasticJ: "#8b5cf6",
};

export function TechnicalChart({ data, visibility }: TechnicalChartProps) {
    const t = useTranslations("StockDetail");

    // Detect dark mode for theme-aware colors
    const [isDark, setIsDark] = useState(true);
    useEffect(() => {
        const checkDark = () => setIsDark(document.documentElement.classList.contains('dark'));
        checkDark();
        const observer = new MutationObserver(checkDark);
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
        return () => observer.disconnect();
    }, []);

    // Theme-aware colors
    const gridColor = isDark ? "#1f2937" : "#e5e7eb";  // gray-800 / gray-200 (subtle grid)
    const borderColor = isDark ? "#374151" : "#d1d5db";  // gray-700 / gray-300
    const textColor = isDark ? "#9ca3af" : "#6b7280";  // gray-400 / gray-500

    const mainChartRef = useRef<HTMLDivElement>(null);
    const volumeChartRef = useRef<HTMLDivElement>(null);
    const rsiChartRef = useRef<HTMLDivElement>(null);
    const macdChartRef = useRef<HTMLDivElement>(null);
    const kdChartRef = useRef<HTMLDivElement>(null);
    const tooltipRef = useRef<HTMLDivElement>(null);

    // Tooltip state for OHLC data
    const [tooltipData, setTooltipData] = useState<{
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
    } | null>(null);

    useEffect(() => {
        if (!mainChartRef.current || !data.ohlcv.length) return;

        // Main candlestick chart
        const mainChart = createChart(mainChartRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: "transparent" },
                textColor: textColor,
            },
            grid: {
                vertLines: { color: gridColor },
                horzLines: { color: gridColor },
            },
            width: mainChartRef.current.clientWidth,
            height: 400,
            crosshair: {
                mode: 1,
            },
            timeScale: {
                borderColor: borderColor,
            },
            rightPriceScale: {
                borderColor: borderColor,
            },
        });

        // Candlestick series
        const candlestickSeries = mainChart.addSeries(CandlestickSeries, {
            upColor: "#22c55e",
            downColor: "#ef4444",
            borderUpColor: "#22c55e",
            borderDownColor: "#ef4444",
            wickUpColor: "#22c55e",
            wickDownColor: "#ef4444",
        });

        const candleData: CandlestickData[] = data.ohlcv.map((d) => ({
            time: d.date as Time,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
        }));
        candlestickSeries.setData(candleData);

        // Subscribe to crosshair move for tooltip
        mainChart.subscribeCrosshairMove((param) => {
            if (!param.time || !param.point || param.point.x < 0 || param.point.y < 0) {
                setTooltipData(null);
                return;
            }

            const dateStr = param.time as string;
            const ohlcvIndex = data.ohlcv.findIndex(d => d.date === dateStr);

            if (ohlcvIndex >= 0) {
                const candle = data.ohlcv[ohlcvIndex];
                const prevClose = ohlcvIndex > 0 ? data.ohlcv[ohlcvIndex - 1].close : candle.open;
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
                });
            }
        });

        // Moving averages with labels
        const addLineSeries = (
            values: (number | null)[],
            color: string,
            visible: boolean,
            title?: string
        ) => {
            if (!visible) return null;
            const series = mainChart.addSeries(LineSeries, {
                color,
                lineWidth: 1,
                priceLineVisible: false,
                title: title || "",
            });
            const lineData: LineData[] = data.ohlcv
                .map((d, i) => ({
                    time: d.date as Time,
                    value: values[i],
                }))
                .filter((d) => d.value !== null) as LineData[];
            series.setData(lineData);
            return series;
        };

        if (visibility.ma) {
            addLineSeries(data.indicators.sma.ma5, INDICATOR_COLORS.ma5, true, "MA5");
            addLineSeries(data.indicators.sma.ma20, INDICATOR_COLORS.ma20, true, "MA20");
            addLineSeries(data.indicators.sma.ma60, INDICATOR_COLORS.ma60, true, "MA60");
        }

        // Bollinger Bands with labels
        if (visibility.bollinger) {
            addLineSeries(data.indicators.bollinger.upper, INDICATOR_COLORS.bollingerUpper, true, "BB Upper");
            addLineSeries(data.indicators.bollinger.middle, INDICATOR_COLORS.bollingerMiddle, true, "BB Mid");
            addLineSeries(data.indicators.bollinger.lower, INDICATOR_COLORS.bollingerLower, true, "BB Lower");
        }

        mainChart.timeScale().fitContent();

        // Volume chart
        let volumeChart: IChartApi | null = null;
        if (visibility.volume && volumeChartRef.current) {
            volumeChart = createChart(volumeChartRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: "transparent" },
                    textColor: textColor,
                },
                grid: {
                    vertLines: { visible: false },
                    horzLines: { color: gridColor },
                },
                width: volumeChartRef.current.clientWidth,
                height: 100,
                timeScale: { visible: false },
            });

            const volumeSeries = volumeChart.addSeries(HistogramSeries, {
                color: INDICATOR_COLORS.volume,
                priceFormat: { type: "volume" },
            });

            const volumeData: HistogramData[] = data.ohlcv.map((d, i) => ({
                time: d.date as Time,
                value: data.indicators.volume[i],
                color: d.close >= d.open ? "#22c55e80" : "#ef444480",
            }));
            volumeSeries.setData(volumeData);
        }

        // RSI chart
        let rsiChart: IChartApi | null = null;
        if (visibility.rsi && rsiChartRef.current) {
            rsiChart = createChart(rsiChartRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: "transparent" },
                    textColor: textColor,
                },
                grid: {
                    vertLines: { visible: false },
                    horzLines: { visible: false },
                },
                rightPriceScale: {
                    scaleMargins: { top: 0.1, bottom: 0.1 },
                    autoScale: false,
                },
                width: rsiChartRef.current.clientWidth,
                height: 100,
                timeScale: { visible: false },
            });

            // Set fixed price range for RSI (0-100)
            rsiChart.priceScale("right").applyOptions({
                autoScale: false,
            });

            const rsiSeries = rsiChart.addSeries(LineSeries, {
                color: INDICATOR_COLORS.rsi,
                lineWidth: 1,
                priceLineVisible: false,
                title: "RSI",
            });

            const rsiData: LineData[] = data.ohlcv
                .map((d, i) => ({
                    time: d.date as Time,
                    value: data.indicators.rsi[i],
                }))
                .filter((d) => d.value !== null) as LineData[];
            rsiSeries.setData(rsiData);

            // Add subtle reference lines at 70, 50, 30
            rsiSeries.createPriceLine({ price: 70, color: gridColor, lineStyle: 1, lineWidth: 1, axisLabelVisible: false });
            rsiSeries.createPriceLine({ price: 50, color: gridColor, lineStyle: 1, lineWidth: 1, axisLabelVisible: false });
            rsiSeries.createPriceLine({ price: 30, color: gridColor, lineStyle: 1, lineWidth: 1, axisLabelVisible: false });
        }

        // MACD chart
        let macdChart: IChartApi | null = null;
        if (visibility.macd && macdChartRef.current) {
            macdChart = createChart(macdChartRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: "transparent" },
                    textColor: textColor,
                },
                grid: {
                    vertLines: { visible: false },
                    horzLines: { color: gridColor },
                },
                width: macdChartRef.current.clientWidth,
                height: 100,
                timeScale: { visible: false },
            });

            // MACD line
            const macdLineSeries = macdChart.addSeries(LineSeries, {
                color: INDICATOR_COLORS.macdLine,
                lineWidth: 1,
                priceLineVisible: false,
                title: "MACD",
            });
            const macdLineData: LineData[] = data.ohlcv
                .map((d, i) => ({
                    time: d.date as Time,
                    value: data.indicators.macd.line[i],
                }))
                .filter((d) => d.value !== null) as LineData[];
            macdLineSeries.setData(macdLineData);

            // Signal line
            const signalSeries = macdChart.addSeries(LineSeries, {
                color: INDICATOR_COLORS.macdSignal,
                lineWidth: 1,
                priceLineVisible: false,
                title: "Signal",
            });
            const signalData: LineData[] = data.ohlcv
                .map((d, i) => ({
                    time: d.date as Time,
                    value: data.indicators.macd.signal[i],
                }))
                .filter((d) => d.value !== null) as LineData[];
            signalSeries.setData(signalData);

            // Histogram
            const histSeries = macdChart.addSeries(HistogramSeries, {
                priceLineVisible: false,
                title: "Hist",
            });
            const histData: HistogramData[] = data.ohlcv
                .map((d, i) => ({
                    time: d.date as Time,
                    value: data.indicators.macd.histogram[i] || 0,
                    color: (data.indicators.macd.histogram[i] || 0) >= 0
                        ? INDICATOR_COLORS.macdHistPos
                        : INDICATOR_COLORS.macdHistNeg,
                }));
            histSeries.setData(histData);
        }

        // KD (Stochastic) chart
        let kdChart: IChartApi | null = null;
        if (visibility.stochastic && kdChartRef.current) {
            kdChart = createChart(kdChartRef.current, {
                layout: {
                    background: { type: ColorType.Solid, color: "transparent" },
                    textColor: textColor,
                },
                grid: {
                    vertLines: { visible: false },
                    horzLines: { visible: false },
                },
                rightPriceScale: {
                    scaleMargins: { top: 0.1, bottom: 0.1 },
                    autoScale: false,
                },
                width: kdChartRef.current.clientWidth,
                height: 100,
                timeScale: { visible: false },
            });

            // Set fixed price range for KD (0-100)
            kdChart.priceScale("right").applyOptions({
                autoScale: false,
            });

            // K line
            const kSeries = kdChart.addSeries(LineSeries, {
                color: INDICATOR_COLORS.stochasticK,
                lineWidth: 1,
                priceLineVisible: false,
                title: "K",
            });
            const kData: LineData[] = data.ohlcv
                .map((d, i) => ({
                    time: d.date as Time,
                    value: data.indicators.stochastic.k[i],
                }))
                .filter((d) => d.value !== null) as LineData[];
            kSeries.setData(kData);

            // D line
            const dSeries = kdChart.addSeries(LineSeries, {
                color: INDICATOR_COLORS.stochasticD,
                lineWidth: 1,
                priceLineVisible: false,
                title: "D",
            });
            const dData: LineData[] = data.ohlcv
                .map((d, i) => ({
                    time: d.date as Time,
                    value: data.indicators.stochastic.d[i],
                }))
                .filter((d) => d.value !== null) as LineData[];
            dSeries.setData(dData);

            // Add subtle reference lines at 80, 50, 20
            kSeries.createPriceLine({ price: 80, color: gridColor, lineStyle: 1, lineWidth: 1, axisLabelVisible: false });
            kSeries.createPriceLine({ price: 50, color: gridColor, lineStyle: 1, lineWidth: 1, axisLabelVisible: false });
            kSeries.createPriceLine({ price: 20, color: gridColor, lineStyle: 1, lineWidth: 1, axisLabelVisible: false });
        }

        // Sync time scales
        const charts = [mainChart, volumeChart, rsiChart, macdChart, kdChart].filter(Boolean) as IChartApi[];
        if (charts.length > 1) {
            const mainTimeScale = mainChart.timeScale();
            charts.slice(1).forEach((chart) => {
                mainTimeScale.subscribeVisibleLogicalRangeChange((range) => {
                    if (range) {
                        chart.timeScale().setVisibleLogicalRange(range);
                    }
                });
            });
        }

        // Handle resize
        const handleResize = () => {
            if (mainChartRef.current) {
                mainChart.applyOptions({ width: mainChartRef.current.clientWidth });
            }
            charts.slice(1).forEach((chart, i) => {
                const refs = [volumeChartRef, rsiChartRef, macdChartRef, kdChartRef];
                const ref = refs[i];
                if (ref.current) {
                    chart.applyOptions({ width: ref.current.clientWidth });
                }
            });
        };
        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            mainChart.remove();
            volumeChart?.remove();
            rsiChart?.remove();
            macdChart?.remove();
            kdChart?.remove();
        };
    }, [data, visibility, isDark]);

    return (
        <div className="space-y-4">
            {/* Main chart */}
            <Card>
                <CardContent className="p-4 relative">
                    <div ref={mainChartRef} />
                    {/* Floating tooltip */}
                    {tooltipData && (
                        <div
                            ref={tooltipRef}
                            className="absolute pointer-events-none z-50 px-3 py-2 rounded-md shadow-lg text-sm
                                       bg-background/90 dark:bg-card/90 border border-border backdrop-blur-sm"
                            style={{
                                left: Math.min(tooltipData.x + 15, (mainChartRef.current?.clientWidth || 300) - 180),
                                top: Math.max(tooltipData.y - 60, 10),
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
                </CardContent>
            </Card>

            {/* Sub-charts */}
            {visibility.volume && (
                <Card>
                    <CardHeader className="py-2 px-4">
                        <CardTitle className="text-sm">Volume</CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
                        <div ref={volumeChartRef} />
                    </CardContent>
                </Card>
            )}

            {visibility.macd && (
                <Card>
                    <CardHeader className="py-2 px-4">
                        <CardTitle className="text-sm">MACD (12, 26, 9)</CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
                        <div ref={macdChartRef} />
                    </CardContent>
                </Card>
            )}

            {visibility.stochastic && (
                <Card>
                    <CardHeader className="py-2 px-4">
                        <CardTitle className="text-sm">KD (9, 3)</CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
                        <div ref={kdChartRef} />
                    </CardContent>
                </Card>
            )}

            {visibility.rsi && (
                <Card>
                    <CardHeader className="py-2 px-4">
                        <CardTitle className="text-sm">RSI (14)</CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
                        <div ref={rsiChartRef} />
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
