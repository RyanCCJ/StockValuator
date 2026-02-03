"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { MarketPulseChart } from "./market-pulse-chart";
import {
    getMarketPulseHistory,
    MarketPulseHistoricalResponse,
} from "@/services/api";

interface MarketPulseSectionProps {
    className?: string;
}

export function MarketPulseSection({ className }: MarketPulseSectionProps) {
    const t = useTranslations("MarketCycle");
    const [data, setData] = useState<MarketPulseHistoricalResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchData() {
            try {
                setIsLoading(true);
                const response = await getMarketPulseHistory("1y");
                setData(response);
            } catch (err) {
                console.error("Failed to fetch market pulse history:", err);
                setError("Failed to load market pulse data");
            } finally {
                setIsLoading(false);
            }
        }

        fetchData();
    }, []);

    return (
        <Card className={className}>
            <CardHeader>
                <CardTitle>{t("market_pulse")}</CardTitle>
                <CardDescription>
                    {t("market_pulse_desc")}
                </CardDescription>
            </CardHeader>
            <CardContent>
                {isLoading ? (
                    <div className="flex items-center justify-center h-64">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                ) : error ? (
                    <div className="flex items-center justify-center h-64 text-muted-foreground">
                        {error}
                    </div>
                ) : (
                    <MarketPulseChart
                        indices={data?.indices || []}
                        isLoading={isLoading}
                    />
                )}
            </CardContent>
        </Card>
    );
}
