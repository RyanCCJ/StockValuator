"use client";

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

export function OverviewCharts({ holdings }: OverviewChartsProps) {
    const t = useTranslations("Dashboard");

    if (!holdings || holdings.length === 0) {
        return null;
    }

    const { formatMoney } = useCurrency();

    // formatMoney is provided by useCurrency() - Note: chart tooltips use shortened format
    const formatChartValue = (value: number) => {
        // For charts, we use a simpler format without full localization
        // This is intentional for chart readability
        return formatMoney(value);
    };

    // Allocation data for pie chart
    const allocationData = holdings.map((h, i) => ({
        name: h.symbol,
        value: h.current_value,
        color: COLORS[i % COLORS.length],
    }));

    // P&L data for bar chart
    const pnlData = holdings.map((h) => ({
        symbol: h.symbol,
        pnl: h.unrealized_pnl,
        pnlPercent: h.unrealized_pnl_percent,
    }));

    // Custom Tooltip
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const CustomTooltip = ({ active, payload, label }: any) => {
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
            {/* Allocation Pie Chart */}
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
                                    data={allocationData}
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
                                    {allocationData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
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
                                    content={<CustomTooltip />}
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
