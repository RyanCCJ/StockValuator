"use client";

import { useMemo } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Holding } from "@/services/api";
import {
    PieChart,
    Pie,
    Cell,
    ResponsiveContainer,
    Tooltip,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
} from "recharts";
import { useCurrency } from "@/context/currency-context";

interface OverviewChartsProps {
    holdings: Holding[];
}

const COLORS = [
    "#5882A6", // Hybrid Blue
    "#5BA468", // Hybrid Green
    "#E39845", // Hybrid Orange
    "#D95C5C", // Hybrid Red
    "#9F7AAD", // Hybrid Purple
    "#76B6B6", // Hybrid Teal
    "#DEC565", // Hybrid Yellow
    "#E8818E", // Hybrid Pink
];

interface SectorData {
    name: string;
    value: number;
    color: string;
    holdings: {
        symbol: string;
        value: number;
        weight: number;
    }[];
    [key: string]: unknown;
}

export function OverviewCharts({ holdings }: OverviewChartsProps) {
    const t = useTranslations("Dashboard");
    const { formatMoney } = useCurrency();

    // Calculate total portfolio value
    const totalPortfolioValue = useMemo(() => {
        return holdings.reduce((sum, h) => sum + h.current_value, 0);
    }, [holdings]);

    // Group holdings by sector and aggregate values
    const sectorAllocationData = useMemo(() => {
        if (!holdings || holdings.length === 0) return [];

        const sectorMap = new Map<string, { value: number; holdings: Holding[] }>();

        for (const holding of holdings) {
            const sector = holding.sector || "Other";
            const existing = sectorMap.get(sector);
            if (existing) {
                existing.value += holding.current_value;
                existing.holdings.push(holding);
            } else {
                sectorMap.set(sector, {
                    value: holding.current_value,
                    holdings: [holding],
                });
            }
        }

        // Convert to array and sort by value (descending)
        const sectorsArray: SectorData[] = Array.from(sectorMap.entries())
            .map(([name, data], index) => ({
                name,
                value: data.value,
                color: COLORS[index % COLORS.length],
                holdings: data.holdings
                    .sort((a, b) => b.current_value - a.current_value)
                    .map((h) => ({
                        symbol: h.symbol,
                        value: h.current_value,
                        weight: totalPortfolioValue > 0
                            ? (h.current_value / totalPortfolioValue) * 100
                            : 0,
                    })),
            }))
            .sort((a, b) => b.value - a.value);

        return sectorsArray;
    }, [holdings, totalPortfolioValue]);

    if (!holdings || holdings.length === 0) {
        return null;
    }

    const formatChartValue = (value: number) => {
        return formatMoney(value);
    };

    // P&L data for bar chart (unchanged)
    const pnlData = holdings.map((h) => ({
        symbol: h.symbol,
        pnl: h.unrealized_pnl,
        pnlPercent: h.unrealized_pnl_percent,
    }));

    // Custom Tooltip for Sector Pie Chart
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SectorTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload as SectorData;
            const sectorWeight = totalPortfolioValue > 0
                ? (data.value / totalPortfolioValue) * 100
                : 0;

            // Sort holdings by value to show top ones first
            const sortedHoldings = [...data.holdings].sort((a, b) => b.value - a.value);
            const topHoldings = sortedHoldings.slice(0, 5);
            const remainingCount = sortedHoldings.length - 5;
            const remainingValue = sortedHoldings.slice(5).reduce((sum, h) => sum + h.value, 0);

            return (
                <div className="rounded-lg border bg-popover/95 px-3 py-2 text-popover-foreground shadow-xl backdrop-blur-sm min-w-[180px]">
                    <div className="font-semibold text-sm mb-1.5 flex justify-between items-center border-b pb-1.5 gap-3">
                        <span className="flex items-center gap-2 truncate">
                            <span className="w-2.5 h-2.5 rounded-full shrink-0 block" style={{ backgroundColor: data.color }}></span>
                            <span className="truncate">{data.name}</span>
                        </span>
                        <span className="text-muted-foreground text-xs font-normal shrink-0">
                            {sectorWeight.toFixed(1)}%
                        </span>
                    </div>
                    <div className="text-base font-bold mb-2">
                        {formatChartValue(data.value)}
                    </div>
                    <div className="space-y-1.5">
                        {topHoldings.map((holding) => (
                            <div key={holding.symbol} className="flex justify-between text-xs items-center">
                                <span className="font-medium text-muted-foreground">{holding.symbol}</span>
                                <div className="flex gap-2 text-right items-center">
                                    <span>{formatChartValue(holding.value)}</span>
                                    <span className="text-muted-foreground text-[10px] w-8 tabular-nums">
                                        {holding.weight.toFixed(1)}%
                                    </span>
                                </div>
                            </div>
                        ))}
                        {remainingCount > 0 && (
                            <div className="flex justify-between text-xs items-center pt-1.5 border-t border-dashed mt-1">
                                <span className="text-muted-foreground italic text-[10px]">+{remainingCount} others</span>
                                <span className="text-[10px]">{formatChartValue(remainingValue)}</span>
                            </div>
                        )}
                    </div>
                </div>
            );
        }
        return null;
    };

    // Custom Tooltip for P&L Bar Chart
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const PnLTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="rounded-lg border bg-popover/90 px-3 py-2 text-popover-foreground shadow-xl backdrop-blur-sm">
                    {label && <div className="font-semibold text-xs mb-1">{label}</div>}
                    {payload.map((entry: any, index: number) => (
                        <div key={index} className="flex gap-2 items-center text-xs">
                            <span className="opacity-70">{entry.name}:</span>
                            <span className="font-medium">{formatChartValue(entry.value)}</span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="grid gap-4 md:grid-cols-2">
            {/* Sector Allocation Pie Chart */}
            <Card>
                <CardHeader>
                    <CardTitle>{t('asset_allocation')}</CardTitle>
                    <CardDescription>{t('portfolio_distribution')}</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-[250px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={sectorAllocationData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={45}
                                    outerRadius={70} // Reduced radius further to prevent labels from being cut off
                                    paddingAngle={3}
                                    dataKey="value"
                                    label={({ cx, cy, midAngle, innerRadius, outerRadius, percent, name, index }) => {
                                        if ((percent ?? 0) < 0.01) return null; // Hide labels for sectors < 1%

                                        const sectorName = name ? String(name) : '';
                                        const RADIAN = Math.PI / 180;
                                        const safeMidAngle = midAngle ?? 0;
                                        const safeOuterRadius = outerRadius ?? 80;

                                        // Revert to 2-level stagger as 3-level was pushing labels off-screen
                                        const isCrowded = sectorAllocationData.length > 4;
                                        const staggerOffset = isCrowded ? (index % 2 === 0 ? 0 : 15) : 0;

                                        const radius = safeOuterRadius + 20 + staggerOffset;
                                        const x = cx + radius * Math.cos(-safeMidAngle * RADIAN);
                                        const y = cy + radius * Math.sin(-safeMidAngle * RADIAN);
                                        const textAnchor = x > cx ? 'start' : 'end';
                                        const percentVal = ((percent ?? 0) * 100).toFixed(0);

                                        // Split name into words to check if wrapping is needed
                                        const words = sectorName.split(' ');
                                        const shouldWrapName = sectorName.length > 10 && words.length > 1;

                                        return (
                                            <text
                                                x={x}
                                                y={y}
                                                fill="currentColor"
                                                textAnchor={textAnchor}
                                                style={{ fontSize: '12px' }}
                                                className="font-medium text-muted-foreground"
                                            >
                                                {shouldWrapName ? (
                                                    <>
                                                        {words.map((word: string, i: number) => (
                                                            <tspan x={x} dy={i === 0 ? "-0.8em" : "1.1em"} key={i}>
                                                                {word}
                                                            </tspan>
                                                        ))}
                                                        <tspan x={x} dy="1.1em" className="font-bold opacity-80">
                                                            {`${percentVal}%`}
                                                        </tspan>
                                                    </>
                                                ) : (
                                                    <>
                                                        <tspan x={x} dy="-0.2em">{sectorName}</tspan>
                                                        <tspan x={x} dy="1.1em" className="font-bold opacity-80">
                                                            {`${percentVal}%`}
                                                        </tspan>
                                                    </>
                                                )}
                                            </text>
                                        );
                                    }}
                                    labelLine={false}
                                >
                                    {sectorAllocationData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip content={<SectorTooltip />} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            {/* P&L Bar Chart */}
            <Card>
                <CardHeader>
                    <CardTitle>{t('unrealized_pnl')}</CardTitle>
                    <CardDescription>{t('by_holding')}</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-[250px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={pnlData} layout="vertical" margin={{ left: 5, right: 5, top: 5, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal vertical={false} strokeOpacity={0.2} />
                                <XAxis
                                    type="number"
                                    tickFormatter={(v) => formatChartValue(v)}
                                    tick={{ fontSize: 11 }}
                                    tickLine={false}
                                    axisLine={false}
                                    className="text-muted-foreground"
                                />
                                <YAxis
                                    type="category"
                                    dataKey="symbol"
                                    width={50}
                                    tick={{ fontSize: 11, fontWeight: 500 }}
                                    tickLine={false}
                                    axisLine={false}
                                    className="text-muted-foreground"
                                />
                                <Tooltip
                                    content={<PnLTooltip />}
                                    cursor={{ fill: "transparent" }}
                                />
                                <Bar dataKey="pnl" name={t('total_pnl')} radius={[0, 4, 4, 0]}>
                                    {pnlData.map((entry, index) => (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={entry.pnl >= 0 ? "#5BA468" : "#D95C5C"}
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
