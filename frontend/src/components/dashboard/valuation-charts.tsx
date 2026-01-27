"use client";

import { useMemo } from "react";
import { useTranslations } from "next-intl";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    ReferenceArea,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { YearValue } from "@/services/api";

interface ValuationChartsProps {
    peHistory?: YearValue[] | null;
    dividendYieldHistory?: YearValue[] | null;
}

interface ChartStats {
    mean: number;
    std: number;
    high: number;
    low: number;
    upperBand: number;
    lowerBand: number;
}

function calculateStats(data: YearValue[]): ChartStats | null {
    if (!data || data.length < 2) return null;

    const values = data.map((d) => d.value).filter((v) => v !== null && v !== undefined && v > 0);
    if (values.length < 2) return null;

    const sum = values.reduce((a, b) => a + b, 0);
    const mean = sum / values.length;
    const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
    const std = Math.sqrt(variance);
    const high = Math.max(...values);
    const low = Math.min(...values);

    return {
        mean,
        std,
        high,
        low,
        upperBand: mean + std,
        lowerBand: Math.max(0, mean - std),
    };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload, label, valueFormatter }: any) {
    if (active && payload && payload.length) {
        return (
            <div className="rounded-lg border bg-popover/95 px-3 py-2 text-popover-foreground shadow-xl backdrop-blur-sm">
                <div className="font-semibold">{label}</div>
                <div className="text-sm opacity-80">{valueFormatter(payload[0].value)}</div>
            </div>
        );
    }
    return null;
}

function ValuationChart({
    title,
    data,
    valueFormatter,
    color,
}: {
    title: string;
    data: YearValue[];
    valueFormatter: (val: number) => string;
    color: string;
}) {
    const t = useTranslations("ValueAnalysis.ValuationCharts");
    const stats = useMemo(() => calculateStats(data), [data]);

    if (!data || data.length === 0) {
        return (
            <div className="flex-1">
                <div className="pb-2">
                    <h3 className="text-base font-semibold">{title}</h3>
                </div>
                <div className="flex items-center justify-center h-[200px] text-muted-foreground text-sm">
                    {t("no_data")}
                </div>
            </div>
        );
    }

    // Prepare chart data sorted by year
    const chartData = [...data].sort((a, b) => a.year - b.year);
    const currentValue = chartData[chartData.length - 1]?.value;

    // Calculate Y-axis domain with padding
    const allValues = chartData.map((d) => d.value).filter((v) => v > 0);
    const yMin = Math.max(0, Math.min(...allValues) * 0.8);
    const yMax = Math.max(...allValues) * 1.1;

    return (
        <div className="flex-1">
            <div className="pb-2">
                <h4 className="text-sm font-medium text-muted-foreground">{title}</h4>
            </div>
            <div>
                <div className="h-[220px] w-full" style={{ minWidth: "100%", minHeight: "220px" }}>
                    <ResponsiveContainer width="100%" height={220}>
                        <LineChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 10 }}>
                            <XAxis
                                dataKey="year"
                                tick={{ fontSize: 11 }}
                                className="text-muted-foreground"
                                tickLine={false}
                            />
                            <YAxis
                                domain={[yMin, yMax]}
                                tick={{ fontSize: 11 }}
                                className="text-muted-foreground"
                                tickLine={false}
                                axisLine={false}
                                tickFormatter={valueFormatter}
                            />
                            <Tooltip
                                content={<CustomTooltip valueFormatter={valueFormatter} />}
                            />

                            {/* Reasonable Range (Mean ± Std) */}
                            {stats && (
                                <ReferenceArea
                                    y1={stats.lowerBand}
                                    y2={stats.upperBand}
                                    fill={color}
                                    fillOpacity={0.1}
                                    stroke="none"
                                />
                            )}

                            {/* Mean Line */}
                            {stats && (
                                <ReferenceLine
                                    y={stats.mean}
                                    stroke={color}
                                    strokeDasharray="5 5"
                                    strokeOpacity={0.7}
                                    label={{
                                        value: "Mean",
                                        position: "insideTopRight",
                                        fontSize: 10,
                                        fill: color,
                                    }}
                                />
                            )}

                            {/* High Line */}
                            {stats && (
                                <ReferenceLine
                                    y={stats.high}
                                    stroke="#ef4444"
                                    strokeDasharray="3 3"
                                    strokeOpacity={0.6}
                                    label={{
                                        value: "High",
                                        position: "insideTopRight",
                                        fontSize: 10,
                                        fill: "#ef4444",
                                    }}
                                />
                            )}

                            {/* Low Line */}
                            {stats && (
                                <ReferenceLine
                                    y={stats.low}
                                    stroke="#22c55e"
                                    strokeDasharray="3 3"
                                    strokeOpacity={0.6}
                                    label={{
                                        value: "Low",
                                        position: "insideBottomRight",
                                        fontSize: 10,
                                        fill: "#22c55e",
                                    }}
                                />
                            )}

                            {/* Main Data Line */}
                            <Line
                                type="monotone"
                                dataKey="value"
                                stroke={color}
                                strokeWidth={2}
                                dot={{ fill: color, strokeWidth: 0, r: 3 }}
                                activeDot={{ r: 5, fill: color }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Legend */}
                {stats && (
                    <div className="flex flex-wrap justify-center gap-4 mt-2 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: color, opacity: 0.2 }} />
                            <span>{t("reasonable_range")}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <svg width="16" height="8" className="flex-shrink-0">
                                <line x1="0" y1="4" x2="16" y2="4" stroke="#ef4444" strokeWidth="2" strokeDasharray="3 2" />
                            </svg>
                            <span>{t("high")}: {valueFormatter(stats.high)}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <svg width="16" height="8" className="flex-shrink-0">
                                <line x1="0" y1="4" x2="16" y2="4" stroke="#22c55e" strokeWidth="2" strokeDasharray="3 2" />
                            </svg>
                            <span>{t("low")}: {valueFormatter(stats.low)}</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export function ValuationCharts({ peHistory, dividendYieldHistory }: ValuationChartsProps) {
    const t = useTranslations("ValueAnalysis.ValuationCharts");

    // Only render if at least one has data
    const hasData = (peHistory && peHistory.length > 0) || (dividendYieldHistory && dividendYieldHistory.length > 0);
    if (!hasData) {
        return null;
    }

    const formatPE = (val: number) => val?.toFixed(1) ?? "N/A";
    const formatYield = (val: number) => `${(val * 100).toFixed(2)}%`;

    return (
        <Card>
            <CardHeader className="pb-2">
                <CardTitle>{t("title")}</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <ValuationChart
                        title={t("pe_ratio")}
                        data={peHistory || []}
                        valueFormatter={formatPE}
                        color="#8b5cf6"
                    />
                    <ValuationChart
                        title={t("dividend_yield")}
                        data={dividendYieldHistory || []}
                        valueFormatter={formatYield}
                        color="#0ea5e9"
                    />
                </div>
            </CardContent>
        </Card>
    );
}
