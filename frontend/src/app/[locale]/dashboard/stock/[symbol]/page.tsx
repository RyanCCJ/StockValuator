"use client";

import { useState, useEffect, use } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";
import { Bell, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    TechnicalChart,
    useIndicatorVisibility,
    STORAGE_KEY_PERIOD
} from "@/components/dashboard/technical-chart";
import { ValueAnalysis } from "@/components/dashboard/value-analysis";
import { ValueScores } from "@/components/dashboard/value-scores";
import { SetAlertDialog } from "@/components/dashboard/set-alert-dialog";
import {
    getTechnicalData,
    getFundamentalData,
    getStockPrice,
} from "@/services/api";

interface StockDetailPageProps {
    params: Promise<{ symbol: string; locale: string }>;
}

export default function StockDetailPage({ params }: StockDetailPageProps) {
    const { symbol, locale } = use(params);
    const upperSymbol = symbol.toUpperCase();

    // All hooks must be called before any conditional returns
    const { data: session, status } = useSession();
    const t = useTranslations("StockDetail");
    const [isAlertDialogOpen, setIsAlertDialogOpen] = useState(false);

    // Period state with localStorage persistence
    const [selectedPeriod, setSelectedPeriod] = useState<"1mo" | "3mo" | "6mo" | "1y" | "2y">(() => {
        if (typeof window !== "undefined") {
            const saved = localStorage.getItem(STORAGE_KEY_PERIOD);
            if (saved && ["1mo", "3mo", "6mo", "1y", "2y"].includes(saved)) {
                return saved as "1mo" | "3mo" | "6mo" | "1y" | "2y";
            }
        }
        return "1y";
    });

    // Save period to localStorage
    useEffect(() => {
        if (typeof window !== "undefined") {
            localStorage.setItem(STORAGE_KEY_PERIOD, selectedPeriod);
        }
    }, [selectedPeriod]);

    // Indicator visibility with localStorage persistence
    const { visibility, toggleIndicator } = useIndicatorVisibility();

    // Fetch current price
    const { data: priceData } = useQuery({
        queryKey: ["stockPrice", upperSymbol],
        queryFn: () => getStockPrice(upperSymbol),
        staleTime: 60000,
        enabled: status === "authenticated",
    });

    // Fetch technical data
    const {
        data: technicalData,
        isLoading: technicalLoading,
        error: technicalError,
    } = useQuery({
        queryKey: ["technicalData", upperSymbol, selectedPeriod],
        queryFn: () => getTechnicalData(upperSymbol, selectedPeriod),
        staleTime: 300000,
        enabled: status === "authenticated",
    });

    // Fetch fundamental data
    const {
        data: fundamentalData,
        isLoading: fundamentalLoading,
        error: fundamentalError,
    } = useQuery({
        queryKey: ["fundamentalData", upperSymbol],
        queryFn: () => getFundamentalData(upperSymbol),
        staleTime: 3600000,
        enabled: status === "authenticated",
    });

    // Now we can have conditional returns after all hooks
    if (status === "loading") {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (!session) {
        redirect(`/${locale}/login`);
    }

    const priceChange = priceData?.change_percent ?? 0;
    const isPositive = priceChange >= 0;

    return (
        <Tabs defaultValue="technical" className="max-w-7xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">{upperSymbol}</h1>
                    {priceData && (
                        <p className="text-muted-foreground flex items-center gap-2">
                            <span className="text-lg font-semibold text-foreground">
                                ${priceData.price.toFixed(2)}
                            </span>
                            <span
                                className={`text-sm font-medium ${isPositive ? "text-green-500" : "text-red-500"
                                    }`}
                            >
                                {isPositive ? "+" : ""}
                                {priceChange.toFixed(2)}%
                            </span>
                        </p>
                    )}
                </div>
                <div className="flex items-center gap-4">
                    <TabsList>
                        <TabsTrigger value="technical">{t("technical_analysis")}</TabsTrigger>
                        <TabsTrigger value="fundamental">{t("value_analysis")}</TabsTrigger>
                    </TabsList>
                    <Button onClick={() => setIsAlertDialogOpen(true)}>
                        <Bell className="h-4 w-4 mr-2" />
                        {t("set_alert")}
                    </Button>
                </div>
            </div>

            <TabsContent value="technical" className="space-y-4">
                {/* Period and Indicator selectors - responsive row layout */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                    {/* Period buttons - left side */}
                    <div className="flex gap-2">
                        {(["1mo", "3mo", "6mo", "1y", "2y"] as const).map((period) => (
                            <Button
                                key={period}
                                variant={selectedPeriod === period ? "default" : "outline"}
                                size="sm"
                                onClick={() => setSelectedPeriod(period)}
                            >
                                {period.toUpperCase()}
                            </Button>
                        ))}
                    </div>

                    {/* Indicator buttons - right side */}
                    <div className="flex gap-2">
                        <Button
                            variant={visibility.ma ? "default" : "outline"}
                            size="sm"
                            onClick={() => toggleIndicator("ma")}
                        >
                            MA
                        </Button>
                        <Button
                            variant={visibility.bollinger ? "default" : "outline"}
                            size="sm"
                            onClick={() => toggleIndicator("bollinger")}
                        >
                            BB
                        </Button>
                        <Button
                            variant={visibility.volume ? "default" : "outline"}
                            size="sm"
                            onClick={() => toggleIndicator("volume")}
                        >
                            Vol
                        </Button>
                        <Button
                            variant={visibility.macd ? "default" : "outline"}
                            size="sm"
                            onClick={() => toggleIndicator("macd")}
                        >
                            MACD
                        </Button>
                        <Button
                            variant={visibility.stochastic ? "default" : "outline"}
                            size="sm"
                            onClick={() => toggleIndicator("stochastic")}
                        >
                            KD
                        </Button>
                        <Button
                            variant={visibility.rsi ? "default" : "outline"}
                            size="sm"
                            onClick={() => toggleIndicator("rsi")}
                        >
                            RSI
                        </Button>
                    </div>
                </div>

                {technicalLoading ? (
                    <Card>
                        <CardContent className="flex items-center justify-center min-h-[400px]">
                            <Loader2 className="h-8 w-8 animate-spin" />
                        </CardContent>
                    </Card>
                ) : technicalError ? (
                    <Card>
                        <CardContent className="flex items-center justify-center min-h-[400px] text-muted-foreground">
                            {t("error_loading_data")}
                        </CardContent>
                    </Card>
                ) : technicalData ? (
                    <TechnicalChart data={technicalData} visibility={visibility} />
                ) : null}
            </TabsContent>

            <TabsContent value="fundamental">
                {fundamentalLoading ? (
                    <Card>
                        <CardContent className="flex items-center justify-center min-h-[400px]">
                            <Loader2 className="h-8 w-8 animate-spin" />
                        </CardContent>
                    </Card>
                ) : fundamentalError ? (
                    <Card>
                        <CardContent className="flex items-center justify-center min-h-[400px] text-muted-foreground">
                            {t("error_loading_data")}
                        </CardContent>
                    </Card>
                ) : fundamentalData ? (
                    <div className="space-y-6">
                        <ValueAnalysis data={fundamentalData} />
                        {!fundamentalData.is_etf && <ValueScores symbol={upperSymbol} />}
                    </div>
                ) : null}
            </TabsContent>

            {/* Alert Dialog */}
            <SetAlertDialog
                open={isAlertDialogOpen}
                onOpenChange={setIsAlertDialogOpen}
                symbol={upperSymbol}
                currentPrice={priceData?.price}
            />
        </Tabs>
    );
}


