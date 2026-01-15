"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PortfolioSummary } from "@/services/api";
import { useCurrency } from "@/context/currency-context";

interface PortfolioBalanceCardProps {
    portfolio: PortfolioSummary | null;
    isLoading?: boolean;
}

export function PortfolioBalanceCard({ portfolio, isLoading }: PortfolioBalanceCardProps) {
    const t = useTranslations("Dashboard");
    const { formatMoney } = useCurrency();

    if (isLoading) {
        return (
            <Card>
                <CardHeader className="pb-2">
                    <div className="h-4 w-24 bg-muted animate-pulse rounded" />
                </CardHeader>
                <CardContent>
                    <div className="h-8 w-32 bg-muted animate-pulse rounded" />
                </CardContent>
            </Card>
        );
    }

    const totalPortfolio = portfolio?.total_portfolio || 0;
    const investedValue = portfolio?.total_value || 0;
    const cashBalance = portfolio?.cash_balance || 0;
    const cashRatio = portfolio?.cash_ratio || 0;
    const investedRatio = 100 - cashRatio;

    return (
        <Card>
            <CardHeader className="pb-2">
                <CardDescription>{t('total_portfolio_allocation')}</CardDescription>
                <CardTitle className="text-2xl">
                    {formatMoney(totalPortfolio)}
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
                {/* Progress bar showing allocation */}
                <div className="w-full h-3 bg-muted rounded-full overflow-hidden flex">
                    <div
                        className="h-full bg-[#5882A6] transition-all"
                        style={{ width: `${investedRatio}%` }}
                    />
                    <div
                        className="h-full bg-[#5BA468] transition-all"
                        style={{ width: `${cashRatio}%` }}
                    />
                </div>

                {/* Legend */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-[#5882A6]" />
                        <div>
                            <div className="text-muted-foreground">{t('invested')}</div>
                            <div className="font-medium">
                                {formatMoney(investedValue)}
                                <span className="text-xs text-muted-foreground ml-1">
                                    ({investedRatio.toFixed(1)}%)
                                </span>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-[#5BA468]" />
                        <div>
                            <div className="text-muted-foreground">{t('cash')}</div>
                            <div className="font-medium">
                                {formatMoney(cashBalance)}
                                <span className="text-xs text-muted-foreground ml-1">
                                    ({cashRatio.toFixed(1)}%)
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
