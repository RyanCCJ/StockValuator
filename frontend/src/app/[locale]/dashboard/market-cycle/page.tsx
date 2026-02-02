"use client";

import { useState, useEffect, useCallback } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw, TrendingUp, TrendingDown } from "lucide-react";
import { PhaseGauge } from "@/components/market-cycle/phase-gauge";
import { IndicatorCards } from "@/components/market-cycle/indicator-card";
import { HistoricalCharts } from "@/components/market-cycle/historical-charts";
import {
    getMarketCycleStatus,
    MarketCycleStatusResponse,
    MarketPulseItem,
} from "@/services/api";

function MarketPulseCard({ item }: { item: MarketPulseItem }) {
    const isPositive = (item.change_percent ?? 0) >= 0;

    return (
        <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
            <div>
                <div className="text-sm font-medium">{item.name}</div>
                <div className="text-xs text-muted-foreground">{item.symbol}</div>
            </div>
            <div className="text-right">
                <div className="font-medium">
                    {item.price?.toLocaleString(undefined, { maximumFractionDigits: 0 }) ?? "N/A"}
                </div>
                <div
                    className={`text-sm flex items-center justify-end gap-1 ${
                        isPositive
                            ? "text-green-600 dark:text-green-400"
                            : "text-red-600 dark:text-red-400"
                    }`}
                >
                    {isPositive ? (
                        <TrendingUp className="h-3 w-3" />
                    ) : (
                        <TrendingDown className="h-3 w-3" />
                    )}
                    {item.change_percent !== null
                        ? `${isPositive ? "+" : ""}${item.change_percent.toFixed(2)}%`
                        : "N/A"}
                </div>
            </div>
        </div>
    );
}

export default function MarketCyclePage() {
    const t = useTranslations("MarketCycle");
    const [data, setData] = useState<MarketCycleStatusResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await getMarketCycleStatus();
            setData(response);
        } catch (err) {
            console.error("Failed to fetch market cycle data:", err);
            setError(t("error"));
        } finally {
            setIsLoading(false);
        }
    }, [t]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <p className="text-muted-foreground">{t("loading")}</p>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
                <p className="text-destructive">{error || t("error")}</p>
                <Button onClick={fetchData} variant="outline">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    {t("refresh")}
                </Button>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">{t("title")}</h1>
                    <p className="text-muted-foreground">{t("subtitle")}</p>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-sm text-muted-foreground">
                        {t("last_updated")}: {new Date(data.last_updated).toLocaleString()}
                    </span>
                    <Button onClick={fetchData} variant="outline" size="sm">
                        <RefreshCw className="h-4 w-4 mr-2" />
                        {t("refresh")}
                    </Button>
                </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Phase Gauge */}
                <Card className="lg:col-span-1">
                    <CardHeader>
                        <CardTitle>{t("current_phase")}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <PhaseGauge
                            phase={data.phase}
                            phaseNumber={data.phase_number}
                            riskLevel={data.risk_level}
                            totalScore={data.total_score}
                        />
                    </CardContent>
                </Card>

                {/* Market Pulse */}
                <Card className="lg:col-span-2">
                    <CardHeader>
                        <CardTitle>{t("market_pulse")}</CardTitle>
                        <CardDescription>
                            {t("subtitle")}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {data.market_pulse.map((item) => (
                                <MarketPulseCard key={item.symbol} item={item} />
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Indicator Cards */}
            <Card>
                <CardHeader>
                    <CardTitle>{t("indicators")}</CardTitle>
                    <CardDescription>
                        {t("subtitle")}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <IndicatorCards indicators={data.indicators} />
                </CardContent>
            </Card>

            {/* Historical Charts */}
            <HistoricalCharts
                shillerPe={data.shiller_pe}
                yieldSpread={data.yield_spread}
                vix={data.vix}
                sp500Price={data.sp500_price}
                sp500Ma200={data.sp500_ma200}
            />
        </div>
    );
}
