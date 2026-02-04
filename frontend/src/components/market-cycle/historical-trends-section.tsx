"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { InteractiveTrendChart } from "./interactive-trend-chart";
import {
    getHistoricalTrends,
    HistoricalTrendsResponse,
    HistoricalTrendData,
} from "@/services/api";

interface HistoricalTrendsSectionProps {
    className?: string;
}

export function HistoricalTrendsSection({ className }: HistoricalTrendsSectionProps) {
    const t = useTranslations("MarketCycle");
    const [data, setData] = useState<HistoricalTrendsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchData() {
            try {
                setIsLoading(true);
                const response = await getHistoricalTrends("1y");
                setData(response);
            } catch (err) {
                console.error("Failed to fetch historical trends:", err);
                setError("Failed to load historical trends");
            } finally {
                setIsLoading(false);
            }
        }

        fetchData();
    }, []);

    // Organize trends by indicator
    const getTrendData = (indicator: string): HistoricalTrendData | undefined => {
        return data?.trends.find((t) => t.indicator === indicator);
    };

    if (isLoading) {
        return (
            <Card className={className}>
                <CardHeader>
                    <CardTitle>{t("historical_charts")}</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-64">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error) {
        return (
            <Card className={className}>
                <CardHeader>
                    <CardTitle>{t("historical_charts")}</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-64 text-muted-foreground">
                        {error}
                    </div>
                </CardContent>
            </Card>
        );
    }

    const sp500Data = getTrendData("sp500");
    const vixData = getTrendData("vix");

    return (
        <Card className={className}>
            <CardHeader>
                <CardTitle>{t("historical_charts")}</CardTitle>
            </CardHeader>
            <CardContent>
                {/* Vertical Layout - S&P 500 on top, VIX below */}
                <div className="space-y-6">
                    {/* S&P 500 with MA20, MA50, MA200 */}
                    <div className="p-4 rounded-lg bg-muted/30">
                        <InteractiveTrendChart
                            title="S&P 500 Index"
                            chartType="candlestick"
                            ohlcData={sp500Data?.ohlc_data}
                            showMA={true}
                            height={300}
                        />
                    </div>

                    {/* VIX with Greed/Fear levels */}
                    <div className="p-4 rounded-lg bg-muted/30">
                        <InteractiveTrendChart
                            title="VIX Index"
                            chartType="candlestick"
                            ohlcData={vixData?.ohlc_data}
                            showVIXLevels={true}
                            height={300}
                        />
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
