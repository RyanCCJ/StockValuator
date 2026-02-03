"use client";

import { useMemo } from "react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
} from "recharts";
import { TrendingUp, TrendingDown } from "lucide-react";
import { IndexHistoricalSeries } from "@/services/api";

// Custom tooltip component with proper styling
interface CustomTooltipProps {
    active?: boolean;
    payload?: readonly {
        dataKey: string;
        value: number;
        color: string;
    }[];
    label?: string | number;
    indices: IndexHistoricalSeries[];
}

function CustomTooltip({ active, payload, label, indices }: CustomTooltipProps) {
    if (!active || !payload || payload.length === 0 || label === undefined) return null;

    return (
        <div className="px-3 py-2 rounded-md shadow-lg text-sm bg-background/90 dark:bg-card/90 border border-border backdrop-blur-sm">
            <div className="font-medium text-foreground mb-1">
                {new Date(String(label)).toLocaleDateString()}
            </div>
            <div className="space-y-0.5">
                {payload.map((entry) => {
                    const index = indices.find((i) => i.symbol === entry.dataKey);
                    const value = entry.value;
                    return (
                        <div key={entry.dataKey} className="flex items-center gap-2 text-xs">
                            <div
                                className="w-2 h-2 rounded-full flex-shrink-0"
                                style={{ backgroundColor: entry.color }}
                            />
                            <span className="text-muted-foreground">{index?.name || entry.dataKey}</span>
                            <span className={`font-medium ${value >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                {value >= 0 ? '+' : ''}{value.toFixed(2)}%
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

interface MarketPulseChartProps {
    indices: IndexHistoricalSeries[];
    isLoading?: boolean;
}

// Color palette for indices - muted scientific color scheme
const INDEX_COLORS: Record<string, string> = {
    "^DJI": "#6b9ac4",    // muted blue
    "^IXIC": "#9d8ec4",   // muted purple
    "^GSPC": "#7cb884",   // muted green
    "^RUT": "#d4915e",    // muted orange
};

interface NormalizedDataPoint {
    date: string;
    [key: string]: number | string;
}

interface PerformanceMetric {
    symbol: string;
    name: string;
    currentValue: number;
    startValue: number;
    change: number;
    changePercent: number;
    color: string;
}

export function MarketPulseChart({ indices, isLoading }: MarketPulseChartProps) {
    // Normalize data to percentage change from baseline (first data point)
    const { chartData, performanceMetrics } = useMemo(() => {
        if (!indices || indices.length === 0) {
            return { chartData: [], performanceMetrics: [] };
        }

        // Find the common date range across all indices
        const allDates = new Set<string>();
        indices.forEach((index) => {
            index.data.forEach((point) => allDates.add(point.date));
        });
        const sortedDates = Array.from(allDates).sort();

        // Create baseline values (first data point for each index)
        const baselines: Record<string, number> = {};
        indices.forEach((index) => {
            if (index.data.length > 0) {
                baselines[index.symbol] = index.data[0].close;
            }
        });

        // Create lookup for quick access
        const dataLookup: Record<string, Record<string, number>> = {};
        indices.forEach((index) => {
            dataLookup[index.symbol] = {};
            index.data.forEach((point) => {
                dataLookup[index.symbol][point.date] = point.close;
            });
        });

        // Build normalized data
        const normalizedData: NormalizedDataPoint[] = sortedDates.map((date) => {
            const point: NormalizedDataPoint = { date };
            indices.forEach((index) => {
                const value = dataLookup[index.symbol]?.[date];
                const baseline = baselines[index.symbol];
                if (value !== undefined && baseline) {
                    // Normalize to percentage change
                    point[index.symbol] = ((value - baseline) / baseline) * 100;
                }
            });
            return point;
        });

        // Calculate performance metrics for legend
        const metrics: PerformanceMetric[] = indices.map((index) => {
            const baseline = baselines[index.symbol] || 0;
            const currentValue = index.data.length > 0 ? index.data[index.data.length - 1].close : 0;
            const change = currentValue - baseline;
            const changePercent = baseline ? ((currentValue - baseline) / baseline) * 100 : 0;

            return {
                symbol: index.symbol,
                name: index.name,
                currentValue,
                startValue: baseline,
                change,
                changePercent,
                color: INDEX_COLORS[index.symbol] || "#888888",
            };
        });

        return { chartData: normalizedData, performanceMetrics: metrics };
    }, [indices]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64 text-muted-foreground">
                Loading chart data...
            </div>
        );
    }

    if (chartData.length === 0) {
        return (
            <div className="flex items-center justify-center h-64 text-muted-foreground">
                No historical data available
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Chart */}
            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 5, right: -20, left: 5, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis
                            dataKey="date"
                            tick={{ fontSize: 10 }}
                            tickFormatter={(value) => {
                                const date = new Date(value);
                                return date.toLocaleDateString("en-US", { month: "short" });
                            }}
                            interval="preserveStartEnd"
                            minTickGap={50}
                            className="text-muted-foreground"
                        />
                        <YAxis
                            orientation="right"
                            tick={{ fontSize: 10 }}
                            tickFormatter={(value) => `${value.toFixed(0)}%`}
                            className="text-muted-foreground"
                            domain={["auto", "auto"]}
                        />
                        <Tooltip
                            content={(props) => <CustomTooltip {...props} indices={indices} />}
                            cursor={{ stroke: 'hsl(var(--muted-foreground))', strokeDasharray: '3 3' }}
                        />
                        <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 3" />
                        {indices.map((index) => (
                            <Line
                                key={index.symbol}
                                type="monotone"
                                dataKey={index.symbol}
                                stroke={INDEX_COLORS[index.symbol] || "#888888"}
                                strokeWidth={2}
                                dot={false}
                                connectNulls
                            />
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Legend with performance metrics (below chart) */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {performanceMetrics.map((metric) => (
                    <div
                        key={metric.symbol}
                        className="flex items-center gap-2 p-2 rounded-lg bg-muted/50"
                    >
                        <div
                            className="w-3 h-3 rounded-full flex-shrink-0"
                            style={{ backgroundColor: metric.color }}
                        />
                        <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium truncate">{metric.name}</div>
                            <div className="flex items-center gap-1">
                                {metric.changePercent >= 0 ? (
                                    <TrendingUp className="h-3 w-3 text-green-500" />
                                ) : (
                                    <TrendingDown className="h-3 w-3 text-red-500" />
                                )}
                                <span
                                    className={`text-xs font-medium ${metric.changePercent >= 0
                                        ? "text-green-600 dark:text-green-400"
                                        : "text-red-600 dark:text-red-400"
                                        }`}
                                >
                                    {metric.changePercent >= 0 ? "+" : ""}
                                    {metric.changePercent.toFixed(2)}%
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
