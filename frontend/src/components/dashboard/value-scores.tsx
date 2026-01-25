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
    getAIScore,
    getAIPrompt,
    ScoreBreakdown,
    FairValueEstimate,
    AIScoreResponse,
    ApiError,
} from "@/services/api";

interface ValueScoresProps {
    symbol: string;
}

function ScoreCard({
    title,
    score,
    maxScore,
    breakdown,
    colorClass,
}: {
    title: string;
    score: number;
    maxScore: number;
    breakdown: ScoreBreakdown[];
    colorClass: string;
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
                    className="w-full flex items-center justify-center gap-2"
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
                        {breakdown.map((item, index) => (
                            <div key={index} className="p-3 bg-muted/50 rounded-lg">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="font-medium text-sm">{item.name}</span>
                                    <span className="text-sm font-semibold">
                                        {item.score}/{item.max_score}
                                    </span>
                                </div>
                                <p className="text-xs text-muted-foreground">{item.reason}</p>
                            </div>
                        ))}
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

function AIScoreSection({
    symbol,
    existingMoatScore,
    existingRiskScore,
}: {
    symbol: string;
    existingMoatScore: number | null;
    existingRiskScore: number | null;
}) {
    const t = useTranslations("ValueAnalysis");
    const [copiedPrompt, setCopiedPrompt] = useState<string | null>(null);
    const [moatResult, setMoatResult] = useState<AIScoreResponse | null>(null);
    const [riskResult, setRiskResult] = useState<AIScoreResponse | null>(null);

    const moatMutation = useMutation({
        mutationFn: () => getAIScore(symbol, "moat"),
        onSuccess: (data) => setMoatResult(data),
    });

    const riskMutation = useMutation({
        mutationFn: () => getAIScore(symbol, "risk"),
        onSuccess: (data) => setRiskResult(data),
    });

    const promptMutation = useMutation({
        mutationFn: (scoreType: "moat" | "risk") => getAIPrompt(symbol, scoreType),
    });

    const handleCopyPrompt = async (scoreType: "moat" | "risk") => {
        try {
            const result = await promptMutation.mutateAsync(scoreType);
            await navigator.clipboard.writeText(result.prompt);
            setCopiedPrompt(scoreType);
            setTimeout(() => setCopiedPrompt(null), 2000);
        } catch {
        }
    };

    const displayMoatScore = moatResult?.score ?? existingMoatScore;
    const displayRiskScore = riskResult?.score ?? existingRiskScore;

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    {t("ai_analysis")}
                </CardTitle>
                <CardDescription>{t("ai_analysis_desc")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="p-4 bg-muted/50 rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="font-medium">{t("moat_score")}</div>
                            <div className="text-sm text-muted-foreground">{t("moat_desc")}</div>
                        </div>
                        {displayMoatScore != null && (
                            <span className="text-xl font-bold text-green-600 dark:text-green-400">
                                +{displayMoatScore}
                            </span>
                        )}
                    </div>
                    <div className="flex gap-2">
                        <Button
                            size="sm"
                            onClick={() => moatMutation.mutate()}
                            disabled={moatMutation.isPending}
                        >
                            {moatMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : null}
                            {t("analyze_moat")}
                        </Button>
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleCopyPrompt("moat")}
                            disabled={promptMutation.isPending}
                        >
                            {copiedPrompt === "moat" ? (
                                <Check className="h-4 w-4 mr-2" />
                            ) : (
                                <Copy className="h-4 w-4 mr-2" />
                            )}
                            {t("copy_prompt")}
                        </Button>
                    </div>
                    {moatResult?.reasoning && (
                        <p className="text-sm text-muted-foreground mt-2">{moatResult.reasoning}</p>
                    )}
                    {moatResult?.manual_entry_required && (
                        <p className="text-sm text-yellow-600 dark:text-yellow-400">
                            {t("manual_entry_required")}
                        </p>
                    )}
                </div>

                <div className="p-4 bg-muted/50 rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="font-medium">{t("risk_score")}</div>
                            <div className="text-sm text-muted-foreground">{t("risk_desc")}</div>
                        </div>
                        {displayRiskScore != null && (
                            <span className="text-xl font-bold text-red-600 dark:text-red-400">
                                {displayRiskScore}
                            </span>
                        )}
                    </div>
                    <div className="flex gap-2">
                        <Button
                            size="sm"
                            onClick={() => riskMutation.mutate()}
                            disabled={riskMutation.isPending}
                        >
                            {riskMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : null}
                            {t("analyze_risk")}
                        </Button>
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleCopyPrompt("risk")}
                            disabled={promptMutation.isPending}
                        >
                            {copiedPrompt === "risk" ? (
                                <Check className="h-4 w-4 mr-2" />
                            ) : (
                                <Copy className="h-4 w-4 mr-2" />
                            )}
                            {t("copy_prompt")}
                        </Button>
                    </div>
                    {riskResult?.reasoning && (
                        <p className="text-sm text-muted-foreground mt-2">{riskResult.reasoning}</p>
                    )}
                    {riskResult?.manual_entry_required && (
                        <p className="text-sm text-yellow-600 dark:text-yellow-400">
                            {t("manual_entry_required")}
                        </p>
                    )}
                </div>
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
                    score={analysisData.confidence.total}
                    maxScore={analysisData.confidence.max_possible}
                    breakdown={analysisData.confidence.breakdown}
                    colorClass={getScoreColorClass(
                        analysisData.confidence.total,
                        analysisData.confidence.max_possible
                    )}
                />
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

            <AIScoreSection
                symbol={symbol}
                existingMoatScore={analysisData.confidence.moat_score}
                existingRiskScore={analysisData.confidence.risk_score}
            />
        </div>
    );
}
