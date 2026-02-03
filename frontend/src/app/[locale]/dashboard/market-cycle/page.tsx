"use client";

import { useState, useEffect, useCallback } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw } from "lucide-react";
import { MarketCycleWave } from "@/components/market-cycle/market-cycle-wave";
import { IndicatorCards } from "@/components/market-cycle/indicator-card";
import { MarketPulseSection } from "@/components/market-cycle/market-pulse-section";
import { HistoricalTrendsSection } from "@/components/market-cycle/historical-trends-section";
import {
    getMarketCycleStatus,
    MarketCycleStatusResponse,
} from "@/services/api";

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
            <div className="flex items-end justify-between">
                <div>
                    <h1 className="text-3xl font-bold">{t("title")}</h1>
                    <p className="text-muted-foreground">{t("subtitle")}</p>
                </div>
                <span className="text-sm text-muted-foreground">
                    {t("last_updated")}: {new Date(data.last_updated).toLocaleString()}
                </span>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Market Pulse - Performance Chart */}
                <MarketPulseSection />

                {/* Market Cycle Wave */}
                <Card>
                    <CardHeader>
                        <CardTitle>{t("card_title")}</CardTitle>
                        <CardDescription>
                            {t("cycle_desc")}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <MarketCycleWave
                            totalScore={data.total_score}
                            sp500Price={data.sp500_price}
                            sp500Ma200={data.sp500_ma200}
                            phase={data.phase}
                            phaseNumber={data.phase_number}
                            riskLevel={data.risk_level}
                        />
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

            {/* Historical Trends - 2x2 Grid */}
            <HistoricalTrendsSection />
        </div>
    );
}
