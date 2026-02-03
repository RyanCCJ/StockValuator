"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    Area,
    AreaChart,
} from "recharts";

interface HistoricalChartsProps {
    shillerPe: number | null;
    yieldSpread: number | null;
    vix: number | null;
    sp500Price: number | null;
    sp500Ma200: number | null;
}

// Placeholder historical data - in production, this would come from the API
const generateHistoricalData = (
    currentValue: number | null,
    months: number = 12,
    volatility: number = 0.1
) => {
    if (currentValue === null) return [];

    const data = [];
    let value = currentValue * (1 - volatility * 2);

    for (let i = months; i >= 0; i--) {
        const date = new Date();
        date.setMonth(date.getMonth() - i);

        value = value + (Math.random() - 0.5) * currentValue * volatility;
        value = Math.max(value, currentValue * 0.5);
        value = Math.min(value, currentValue * 1.5);

        data.push({
            date: date.toLocaleDateString("en-US", { month: "short", year: "2-digit" }),
            value: parseFloat(value.toFixed(2)),
        });
    }

    // Set the last value to current
    if (data.length > 0) {
        data[data.length - 1].value = currentValue;
    }

    return data;
};

function ChartPlaceholder({ message }: { message: string }) {
    return (
        <div className="flex items-center justify-center h-64 text-muted-foreground">
            {message}
        </div>
    );
}

export function HistoricalCharts({
    shillerPe,
    yieldSpread,
    vix,
    sp500Price,
    sp500Ma200,
}: HistoricalChartsProps) {
    const t = useTranslations("MarketCycle");

    const peData = generateHistoricalData(shillerPe, 24, 0.05);
    const yieldData = generateHistoricalData(yieldSpread, 24, 0.3);
    const vixData = generateHistoricalData(vix, 12, 0.2);
    const sp500Data = generateHistoricalData(sp500Price, 12, 0.03);

    return (
        <Card>
            <CardHeader>
                <CardTitle>{t("historical_charts")}</CardTitle>
            </CardHeader>
            <CardContent>
                <Tabs defaultValue="pe" className="w-full">
                    <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="pe">Shiller PE</TabsTrigger>
                        <TabsTrigger value="yield">Yield Curve</TabsTrigger>
                        <TabsTrigger value="vix">VIX</TabsTrigger>
                        <TabsTrigger value="sp500">S&P 500</TabsTrigger>
                    </TabsList>

                    <TabsContent value="pe" className="mt-4">
                        {peData.length > 0 ? (
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={peData}>
                                        <defs>
                                            <linearGradient id="peGradient" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#8884d8" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                        <XAxis
                                            dataKey="date"
                                            tick={{ fontSize: 12 }}
                                            className="text-muted-foreground"
                                        />
                                        <YAxis
                                            domain={[10, 40]}
                                            tick={{ fontSize: 12 }}
                                            className="text-muted-foreground"
                                        />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: "hsl(var(--background))",
                                                border: "1px solid hsl(var(--border))",
                                            }}
                                        />
                                        <ReferenceLine
                                            y={30}
                                            stroke="#ef4444"
                                            strokeDasharray="5 5"
                                            label={{ value: "Overvalued", position: "right", fontSize: 10 }}
                                        />
                                        <ReferenceLine
                                            y={15}
                                            stroke="#22c55e"
                                            strokeDasharray="5 5"
                                            label={{ value: "Undervalued", position: "right", fontSize: 10 }}
                                        />
                                        <Area
                                            type="monotone"
                                            dataKey="value"
                                            stroke="#8884d8"
                                            fill="url(#peGradient)"
                                            strokeWidth={2}
                                        />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <ChartPlaceholder message="No PE data available" />
                        )}
                    </TabsContent>

                    <TabsContent value="yield" className="mt-4">
                        {yieldData.length > 0 ? (
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={yieldData}>
                                        <defs>
                                            <linearGradient id="yieldGradient" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                        <XAxis
                                            dataKey="date"
                                            tick={{ fontSize: 12 }}
                                            className="text-muted-foreground"
                                        />
                                        <YAxis
                                            domain={[-2, 3]}
                                            tick={{ fontSize: 12 }}
                                            className="text-muted-foreground"
                                        />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: "hsl(var(--background))",
                                                border: "1px solid hsl(var(--border))",
                                            }}
                                            formatter={(value) => value !== undefined ? [`${Number(value).toFixed(2)}%`, "Spread"] : ["N/A", "Spread"]}
                                        />
                                        <ReferenceLine
                                            y={0}
                                            stroke="#ef4444"
                                            strokeWidth={2}
                                            label={{ value: "Inversion", position: "right", fontSize: 10 }}
                                        />
                                        <Area
                                            type="monotone"
                                            dataKey="value"
                                            stroke="#22c55e"
                                            fill="url(#yieldGradient)"
                                            strokeWidth={2}
                                        />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <ChartPlaceholder message="No yield data available" />
                        )}
                    </TabsContent>

                    <TabsContent value="vix" className="mt-4">
                        {vixData.length > 0 ? (
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={vixData}>
                                        <defs>
                                            <linearGradient id="vixGradient" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                                                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                        <XAxis
                                            dataKey="date"
                                            tick={{ fontSize: 12 }}
                                            className="text-muted-foreground"
                                        />
                                        <YAxis
                                            domain={[10, 50]}
                                            tick={{ fontSize: 12 }}
                                            className="text-muted-foreground"
                                        />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: "hsl(var(--background))",
                                                border: "1px solid hsl(var(--border))",
                                            }}
                                        />
                                        <ReferenceLine
                                            y={30}
                                            stroke="#ef4444"
                                            strokeDasharray="5 5"
                                            label={{ value: "High Fear", position: "right", fontSize: 10 }}
                                        />
                                        <ReferenceLine
                                            y={15}
                                            stroke="#eab308"
                                            strokeDasharray="5 5"
                                            label={{ value: "Complacent", position: "right", fontSize: 10 }}
                                        />
                                        <Area
                                            type="monotone"
                                            dataKey="value"
                                            stroke="#f97316"
                                            fill="url(#vixGradient)"
                                            strokeWidth={2}
                                        />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <ChartPlaceholder message="No VIX data available" />
                        )}
                    </TabsContent>

                    <TabsContent value="sp500" className="mt-4">
                        {sp500Data.length > 0 ? (
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={sp500Data}>
                                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                        <XAxis
                                            dataKey="date"
                                            tick={{ fontSize: 12 }}
                                            className="text-muted-foreground"
                                        />
                                        <YAxis
                                            domain={["auto", "auto"]}
                                            tick={{ fontSize: 12 }}
                                            className="text-muted-foreground"
                                            tickFormatter={(value) => value.toLocaleString()}
                                        />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: "hsl(var(--background))",
                                                border: "1px solid hsl(var(--border))",
                                            }}
                                            formatter={(value) => value !== undefined ? [Number(value).toLocaleString(), "S&P 500"] : ["N/A", "S&P 500"]}
                                        />
                                        {sp500Ma200 && (
                                            <ReferenceLine
                                                y={sp500Ma200}
                                                stroke="#3b82f6"
                                                strokeDasharray="5 5"
                                                label={{ value: "200 MA", position: "right", fontSize: 10 }}
                                            />
                                        )}
                                        <Line
                                            type="monotone"
                                            dataKey="value"
                                            stroke="#22c55e"
                                            strokeWidth={2}
                                            dot={false}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <ChartPlaceholder message="No S&P 500 data available" />
                        )}
                    </TabsContent>
                </Tabs>
            </CardContent>
        </Card>
    );
}
