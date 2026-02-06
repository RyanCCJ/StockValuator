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

            return (
                <div className="rounded-lg border bg-popover/95 px-4 py-3 text-popover-foreground shadow-xl backdrop-blur-sm min-w-[200px]">
                    <div className="font-semibold text-base mb-2 flex justify-between items-center">
                        <span>{data.name}</span>
                        <span className="text-muted-foreground text-sm">
                            {sectorWeight.toFixed(1)}%
                        </span>
                    </div>
                    <div className="text-sm mb-3">
                        {formatChartValue(data.value)}
                    </div>
                    <div className="border-t pt-2 space-y-1.5">
                        {data.holdings.map((holding) => (
                            <div key={holding.symbol} className="flex justify-between text-sm">
                                <span className="text-muted-foreground">{holding.symbol}</span>
                                <div className="flex gap-3">
                                    <span>{formatChartValue(holding.value)}</span>
                                    <span className="text-muted-foreground w-12 text-right">
                                        {holding.weight.toFixed(1)}%
                                    </span>
                                </div>
                            </div>
                        ))}
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
                    {label && <div className="font-semibold mb-1">{label}</div>}
                    {payload.map((entry: any, index: number) => (
                        <div key={index} className="flex gap-2 items-center text-sm">
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
                                    innerRadius={50}
                                    outerRadius={80}
                                    paddingAngle={2}
                                    dataKey="value"
                                    label={({ name, percent }) =>
                                        `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                                    }
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
                            <BarChart data={pnlData} layout="vertical" margin={{ left: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal vertical={false} />
                                <XAxis type="number" tickFormatter={(v) => formatChartValue(v)} />
                                <YAxis type="category" dataKey="symbol" width={50} />
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
