"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Loader2, ChevronDown, ChevronUp, Copy, Check, Sparkles, AlertTriangle } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
    getValueAnalysis,
    getFairValue,
    getAIPrompt,
    ScoreBreakdown,
    FairValueEstimate,
    AIScoreResponse,
    ApiError,
} from "@/services/api";

interface ValueScoresProps {
    symbol: string;
}

const SCORE_NAME_MAPPING: Record<string, string> = {
    // Confidence Score
    "EPS": "eps",
    "Dividends": "dividends",
    "FCF": "fcf",
    "ROE": "roe",
    "Interest Coverage": "interest_coverage",
    "Net Margin": "net_margin",

    // Dividend Score
    "Dividend Growth": "dividend_growth",
    "5Y Dividend Growth": "dividend_growth_5y",
    "Growth Acceleration": "growth_acceleration",
    "FCF Payout": "fcf_payout",
    "EPS Payout": "eps_payout",
    "EPS Stability": "eps_stability",
    "Buyback": "buyback",
    "Avg ROE": "avg_roe",
    "Beta": "beta",

    // Value Score
    "Yield vs History": "yield_vs_history",
    "PE vs History": "pe_vs_history",
    "High Yield": "high_yield",
    "Yield vs S&P500": "yield_vs_sp500",
    "Chowder Rule": "chowder_rule",
    "FCF Yield": "fcf_yield",
    "Low PE": "low_pe",
    "PE+ROE Combo": "pe_roe_combo",
    "PE vs S&P500": "low_pe", // Fallback if backend sends different variation
};

function ScoreCard({
    title,
    score,
    maxScore,
    breakdown,
    colorClass,
    children,
}: {
    title: string;
    score: number;
    maxScore: number;
    breakdown: ScoreBreakdown[];
    colorClass: string;
    children?: React.ReactNode;
}) {
    const [isExpanded, setIsExpanded] = useState(false);
    const t = useTranslations("ValueAnalysis");
    const percentage = maxScore > 0 ? (score / maxScore) * 100 : 0;

    return (
        <Card>
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{title}</CardTitle>
                    <span className="text-xl font-bold">
                        {score}/{maxScore}
                    </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden mt-2">
                    <div
                        className={`h-full ${colorClass} transition-all duration-300`}
                        style={{ width: `${percentage}%` }}
                    />
                </div>
            </CardHeader>
            <CardContent>
                <Button
                    variant="ghost"
                    size="sm"
                    className="w-full flex items-center justify-center gap-2 mt-2"
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    {isExpanded ? (
                        <>
                            {t("collapse")} <ChevronUp className="h-4 w-4" />
                        </>
                    ) : (
                        <>
                            {t("expand")} <ChevronDown className="h-4 w-4" />
                        </>
                    )}
                </Button>
                {isExpanded && (
                    <div className="mt-4 space-y-3">
                        {breakdown.map((item, index) => {
                            // Try to get translation key from mapping
                            const mappingKey = SCORE_NAME_MAPPING[item.name];
                            // If key exists, translate it using ScoreNames namespace
                            // Otherwise fallback to original name
                            const displayName = mappingKey
                                ? t(`ScoreNames.${mappingKey}`)
                                : item.name;

                            return (
                                <div key={index} className="p-3 bg-muted/50 rounded-lg">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="font-medium text-sm">{displayName}</span>
                                        <span className="text-sm font-semibold">
                                            {item.score}/{item.max_score}
                                        </span>
                                    </div>
                                    <p className="text-xs text-muted-foreground">{item.reason}</p>
                                </div>
                            );
                        })}
                        {children}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

function getScoreColorClass(score: number, maxScore: number): string {
    const percentage = maxScore > 0 ? (score / maxScore) * 100 : 0;
    if (percentage >= 70) return "bg-green-500";
    if (percentage >= 40) return "bg-yellow-500";
    return "bg-red-500";
}

function MoatRiskInputs({
    symbol,
    localMoatScore,
    localRiskScore,
    onMoatChange,
    onRiskChange,
}: {
    symbol: string;
    localMoatScore: number | "";
    localRiskScore: number | "";
    onMoatChange: (val: number | "") => void;
    onRiskChange: (val: number | "") => void;
}) {
    const t = useTranslations("ValueAnalysis");
    const [copiedPrompt, setCopiedPrompt] = useState<string | null>(null);

    // Prefetch prompts to allow synchronous copy
    const { data: moatData, isLoading: isLoadingMoat } = useQuery({
        queryKey: ["aiPrompt", symbol, "moat"],
        queryFn: () => getAIPrompt(symbol, "moat"),
        staleTime: Infinity, // Prompts don't change often
    });

    const { data: riskData, isLoading: isLoadingRisk } = useQuery({
        queryKey: ["aiPrompt", symbol, "risk"],
        queryFn: () => getAIPrompt(symbol, "risk"),
        staleTime: Infinity,
    });

    const copyToClipboard = async (text: string, scoreType: "moat" | "risk") => {
        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(text);
            } else {
                throw new Error("Clipboard API unavailable");
            }
        } catch (err) {
            console.warn("Clipboard API failed, trying fallback...", err);
            // Fallback for non-secure contexts or failures
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-9999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                document.execCommand("copy");
            } catch (fallbackErr) {
                console.error("Fallback copy failed:", fallbackErr);
                return;
            } finally {
                document.body.removeChild(textArea);
            }
        }

        setCopiedPrompt(scoreType);
        setTimeout(() => setCopiedPrompt(null), 2000);
    };

    return (
        <div className="space-y-3 mt-3">
            {/* Moat Score Row */}
            <div className="p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm flex items-center gap-2">
                        {t("moat_score")}
                    </span>
                    <div className="flex items-center gap-1">
                        <input
                            type="number"
                            min="0"
                            max="5"
                            className="w-12 p-1 h-7 rounded-sm border text-right text-sm bg-background focus:ring-1 focus:ring-primary"
                            value={localMoatScore}
                            onChange={(e) => {
                                const val = e.target.value === "" ? "" : Number(e.target.value);
                                if (val === "" || (val >= 0 && val <= 5)) {
                                    onMoatChange(val);
                                }
                            }}
                            placeholder="0"
                        />
                        <span className="text-sm font-semibold text-muted-foreground">/5</span>
                    </div>
                </div>
                <div className="flex items-center justify-between">
                    <p className="text-xs text-muted-foreground">
                        {t("ai_scoring_hint")}
                    </p>
                    <Button
                        variant="outline"
                        size="sm"
                        className="h-7 px-2 text-xs"
                        onClick={() => moatData && copyToClipboard(moatData.prompt, "moat")}
                        disabled={isLoadingMoat || !moatData}
                        title={t("copy_prompt")}
                    >
                        {isLoadingMoat ? (
                            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        ) : copiedPrompt === "moat" ? (
                            <Check className="h-3 w-3 mr-1 text-green-500" />
                        ) : (
                            <Copy className="h-3 w-3 mr-1" />
                        )}
                        {copiedPrompt === "moat" ? t("copied") : t("copy_prompt")}
                    </Button>
                </div>
            </div>

            {/* Risk Score Row */}
            <div className="p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm flex items-center gap-2">
                        {t("risk_score")}
                    </span>
                    <div className="flex items-center gap-1">
                        <input
                            type="number"
                            min="-3"
                            max="0"
                            className="w-12 p-1 h-7 rounded-sm border text-right text-sm bg-background focus:ring-1 focus:ring-primary"
                            value={localRiskScore}
                            onChange={(e) => {
                                const val = e.target.value === "" ? "" : Number(e.target.value);
                                if (val === "" || (val >= -3 && val <= 0)) {
                                    onRiskChange(val);
                                }
                            }}
                            placeholder="0"
                        />
                        <span className="text-sm font-semibold text-muted-foreground">/0</span>
                    </div>
                </div>
                <div className="flex items-center justify-between">
                    <p className="text-xs text-muted-foreground">
                        {t("ai_scoring_hint")}
                    </p>
                    <Button
                        variant="outline"
                        size="sm"
                        className="h-7 px-2 text-xs"
                        onClick={() => riskData && copyToClipboard(riskData.prompt, "risk")}
                        disabled={isLoadingRisk || !riskData}
                        title={t("copy_prompt")}
                    >
                        {isLoadingRisk ? (
                            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        ) : copiedPrompt === "risk" ? (
                            <Check className="h-3 w-3 mr-1 text-green-500" />
                        ) : (
                            <Copy className="h-3 w-3 mr-1" />
                        )}
                        {copiedPrompt === "risk" ? t("copied") : t("copy_prompt")}
                    </Button>
                </div>
            </div>
        </div>
    );
}

function FairValueSection({
    symbol,
    initialFairValue,
}: {
    symbol: string;
    initialFairValue?: FairValueEstimate;
}) {
    const t = useTranslations("ValueAnalysis");
    const [selectedModel, setSelectedModel] = useState<"growth" | "dividend" | "asset">(
        initialFairValue?.model || "growth"
    );

    const { data: fairValue, isLoading } = useQuery({
        queryKey: ["fairValue", symbol, selectedModel],
        queryFn: () => getFairValue(symbol, selectedModel),
        initialData: initialFairValue?.model === selectedModel ? initialFairValue : undefined,
        staleTime: 300000,
    });

    const models: Array<{ key: "growth" | "dividend" | "asset"; label: string }> = [
        { key: "growth", label: t("growth_model") },
        { key: "dividend", label: t("dividend_model") },
        { key: "asset", label: t("asset_model") },
    ];

    return (
        <Card>
            <CardHeader>
                <CardTitle>{t("fair_value")}</CardTitle>
                <CardDescription>{t("fair_value_desc")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="flex gap-2">
                    {models.map((model) => (
                        <Button
                            key={model.key}
                            variant={selectedModel === model.key ? "default" : "outline"}
                            size="sm"
                            onClick={() => setSelectedModel(model.key)}
                        >
                            {model.label}
                        </Button>
                    ))}
                </div>

                {isLoading ? (
                    <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                ) : fairValue ? (
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 bg-muted/50 rounded-lg text-center">
                                <div className="text-sm text-muted-foreground">{t("fair_value")}</div>
                                <div className="text-2xl font-bold">
                                    {fairValue.fair_value != null
                                        ? `$${fairValue.fair_value.toFixed(2)}`
                                        : "N/A"}
                                </div>
                            </div>
                            <div className="p-4 bg-muted/50 rounded-lg text-center">
                                <div className="text-sm text-muted-foreground">{t("current_price")}</div>
                                <div className="text-2xl font-bold">
                                    {fairValue.current_price != null
                                        ? `$${fairValue.current_price.toFixed(2)}`
                                        : "N/A"}
                                </div>
                            </div>
                        </div>
                        <div
                            className={`p-3 rounded-lg text-center font-medium ${fairValue.is_undervalued
                                ? "bg-green-500/10 text-green-600 dark:text-green-400"
                                : "bg-red-500/10 text-red-600 dark:text-red-400"
                                }`}
                        >
                            {fairValue.is_undervalued ? t("undervalued") : t("overvalued")}
                        </div>
                        <p className="text-sm text-muted-foreground">{fairValue.explanation}</p>
                    </div>
                ) : (
                    <div className="text-center text-muted-foreground py-4">{t("no_data")}</div>
                )}
            </CardContent>
        </Card>
    );
}

export function ValueScores({ symbol }: ValueScoresProps) {
    const t = useTranslations("ValueAnalysis");
    const [retryCount, setRetryCount] = useState(0);
    const [isFetching, setIsFetching] = useState(false);
    const [elapsedSeconds, setElapsedSeconds] = useState(0);
    const [loadingPhase, setLoadingPhase] = useState<"initial" | "fetching">("initial");
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    const estimatedTime = 20;

    const {
        data: analysisData,
        isLoading,
        isFetching: isQueryFetching,
        error,
    } = useQuery({
        queryKey: ["valueAnalysis", symbol, retryCount],
        queryFn: () => getValueAnalysis(symbol),
        staleTime: 300000,
        retry: false,
    });

    useEffect(() => {
        if (isLoading || isFetching || isQueryFetching) {
            setElapsedSeconds(0);
            timerRef.current = setInterval(() => {
                setElapsedSeconds((s) => s + 1);
            }, 1000);
        }

        return () => {
            if (timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
            }
        };
    }, [isLoading, isFetching, isQueryFetching]);

    // State for local scores - defaults to 0
    const [localMoatScore, setLocalMoatScore] = useState<number | "">(0);
    const [localRiskScore, setLocalRiskScore] = useState<number | "">(0);

    // Load from localStorage on mount
    useEffect(() => {
        const savedMoat = localStorage.getItem(`moat_${symbol}`);
        const savedRisk = localStorage.getItem(`risk_${symbol}`);

        // If saved, use saved. If not (and mount), keep default 0.
        // Wait, standard practice for localStorage sync:
        if (savedMoat !== null) {
            setLocalMoatScore(Number(savedMoat));
        } else {
            // Ensure it's 0 if nothing saved
            setLocalMoatScore(0);
        }

        if (savedRisk !== null) {
            setLocalRiskScore(Number(savedRisk));
        } else {
            setLocalRiskScore(0);
        }
    }, [symbol]);

    // Save to localStorage
    const handleMoatChange = (val: number | "") => {
        setLocalMoatScore(val);
        if (val === "") localStorage.removeItem(`moat_${symbol}`);
        else localStorage.setItem(`moat_${symbol}`, String(val));
    };

    const handleRiskChange = (val: number | "") => {
        setLocalRiskScore(val);
        if (val === "") localStorage.removeItem(`risk_${symbol}`);
        else localStorage.setItem(`risk_${symbol}`, String(val));
    };

    const handleRetry = async () => {
        setIsFetching(true);
        setLoadingPhase("fetching");
        try {
            await fetch(`/api/analysis/${symbol}/prefetch`, { method: "POST" });
            await new Promise((resolve) => setTimeout(resolve, 2000));

            for (let i = 0; i < 30; i++) {
                const statusRes = await fetch(`/api/analysis/${symbol}/status`);
                const status = await statusRes.json();

                if (status.cached) {
                    setRetryCount((c) => c + 1);
                    return;
                }

                if (!status.fetching) {
                    break;
                }

                await new Promise((resolve) => setTimeout(resolve, 2000));
            }

            setRetryCount((c) => c + 1);
        } finally {
            setIsFetching(false);
        }
    };

    const progressPercent = Math.min((elapsedSeconds / estimatedTime) * 100, 95);

    if (isLoading || isFetching) {
        return (
            <Card>
                <CardContent className="flex flex-col items-center justify-center min-h-[300px] gap-6 py-12">
                    <div className="relative">
                        <Loader2 className="h-12 w-12 animate-spin text-primary" />
                    </div>

                    <div className="text-center space-y-2">
                        <p className="text-lg font-medium">
                            {t("loading_analysis")}
                        </p>
                        <p className="text-3xl font-mono font-bold text-primary">
                            {elapsedSeconds}s
                        </p>
                    </div>

                    <div className="w-full max-w-xs space-y-2">
                        <Progress value={progressPercent} className="h-2" />
                        <p className="text-xs text-center text-muted-foreground">
                            {t("estimated_time", { seconds: estimatedTime })}
                        </p>
                    </div>

                    <p className="text-sm text-muted-foreground text-center max-w-md">
                        {loadingPhase === "fetching"
                            ? t("fetching_data")
                            : t("loading_first_time")
                        }
                    </p>
                </CardContent>
            </Card>
        );
    }

    if (error || !analysisData) {
        const is404 = error instanceof ApiError && error.status === 404;

        return (
            <Card>
                <CardContent className="flex flex-col items-center justify-center min-h-[300px] gap-4 py-8">
                    {is404 ? (
                        <>
                            <AlertTriangle className="h-12 w-12 text-yellow-500" />
                            <div className="text-center space-y-2">
                                <p className="text-lg font-medium text-yellow-600 dark:text-yellow-400">
                                    {t("symbol_not_found_title")}
                                </p>
                                <p className="text-sm text-muted-foreground max-w-md">
                                    {t("symbol_not_found_description")}
                                </p>
                            </div>
                        </>
                    ) : (
                        <>
                            <p className="text-muted-foreground">{t("error_loading")}</p>
                            <Button onClick={handleRetry} disabled={isFetching}>
                                {t("retry")}
                            </Button>
                        </>
                    )}
                </CardContent>
            </Card>
        );
    }

    // Calculate total confidence score including manual inputs
    const combinedConfidenceScore = analysisData.confidence.total +
        (typeof localMoatScore === "number" ? localMoatScore : 0) +
        (typeof localRiskScore === "number" ? localRiskScore : 0);

    // Max possible is Backend Max (11) + Moat Max (5) = 16
    const combinedMaxScore = analysisData.confidence.max_possible + 5;

    return (
        <div className="space-y-6">
            {analysisData.data_status === "insufficient" && (
                <Card className="border-yellow-500/50 bg-yellow-500/10">
                    <CardContent className="flex items-start gap-4 py-4">
                        <AlertTriangle className="h-6 w-6 text-yellow-500 flex-shrink-0 mt-0.5" />
                        <div className="space-y-1">
                            <p className="font-medium text-yellow-600 dark:text-yellow-400">
                                {t("data_unavailable_title")}
                            </p>
                            <p className="text-sm text-muted-foreground">
                                {t("data_unavailable_description")}
                            </p>
                        </div>
                    </CardContent>
                </Card>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <ScoreCard
                    title={t("confidence_score")}
                    score={combinedConfidenceScore}
                    maxScore={combinedMaxScore}
                    breakdown={analysisData.confidence.breakdown}
                    colorClass={
                        combinedConfidenceScore >= 7
                            ? "bg-green-500"
                            : getScoreColorClass(
                                combinedConfidenceScore,
                                combinedMaxScore
                            )
                    }
                >
                    <MoatRiskInputs
                        symbol={symbol}
                        localMoatScore={localMoatScore}
                        localRiskScore={localRiskScore}
                        onMoatChange={handleMoatChange}
                        onRiskChange={handleRiskChange}
                    />
                </ScoreCard>
                <ScoreCard
                    title={t("dividend_score")}
                    score={analysisData.dividend.total}
                    maxScore={analysisData.dividend.max_possible}
                    breakdown={analysisData.dividend.breakdown}
                    colorClass={getScoreColorClass(
                        analysisData.dividend.total,
                        analysisData.dividend.max_possible
                    )}
                />
                <ScoreCard
                    title={t("value_score")}
                    score={analysisData.value.total}
                    maxScore={analysisData.value.max_possible}
                    breakdown={analysisData.value.breakdown}
                    colorClass={getScoreColorClass(
                        analysisData.value.total,
                        analysisData.value.max_possible
                    )}
                />
            </div>

            <FairValueSection symbol={symbol} initialFairValue={analysisData.fair_value} />
        </div>
    );
}
