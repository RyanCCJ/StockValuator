"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PortfolioSummary } from "@/services/api";
import { useCurrency } from "@/context/currency-context";

interface KPICardsProps {
    portfolio: PortfolioSummary | null;
}

export function KPICards({ portfolio }: KPICardsProps) {
    const t = useTranslations("Dashboard");
    const { formatMoney } = useCurrency();

    // formatMoney is now provided by useCurrency()

    const formatPercent = (value: number) => {
        const sign = value >= 0 ? "+" : "";
        return `${sign}${value.toFixed(2)}%`;
    };

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="pb-2">
                    <CardDescription>{t('total_portfolio_value')}</CardDescription>
                    <CardTitle className="text-2xl">
                        {formatMoney(portfolio?.total_value || 0)}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-xs text-muted-foreground">
                        {t('holdings_count', { count: portfolio?.holdings_count || 0 })}
                    </p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="pb-2">
                    <CardDescription>{t('total_pnl')}</CardDescription>
                    <CardTitle
                        className={`text-2xl ${(portfolio?.total_pnl || 0) >= 0
                            ? "text-green-600 dark:text-green-400"
                            : "text-red-600 dark:text-red-400"
                            }`}
                    >
                        {formatMoney(portfolio?.total_pnl || 0)}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p
                        className={`text-xs ${(portfolio?.total_pnl_percent || 0) >= 0
                            ? "text-green-600 dark:text-green-400"
                            : "text-red-600 dark:text-red-400"
                            }`}
                    >
                        {formatPercent(portfolio?.total_pnl_percent || 0)}
                    </p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="pb-2">
                    <CardDescription>{t('unrealized_pnl')}</CardDescription>
                    <CardTitle
                        className={`text-2xl ${(portfolio?.unrealized_pnl || 0) >= 0
                            ? "text-green-600 dark:text-green-400"
                            : "text-red-600 dark:text-red-400"
                            }`}
                    >
                        {formatMoney(portfolio?.unrealized_pnl || 0)}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-xs text-muted-foreground">{t('open_positions')}</p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="pb-2">
                    <CardDescription>{t('realized_pnl')}</CardDescription>
                    <CardTitle
                        className={`text-2xl ${(portfolio?.realized_pnl || 0) >= 0
                            ? "text-green-600 dark:text-green-400"
                            : "text-red-600 dark:text-red-400"
                            }`}
                    >
                        {formatMoney(portfolio?.realized_pnl || 0)}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-xs text-muted-foreground">{t('closed_positions')}</p>
                </CardContent>
            </Card>
        </div>
    );
}
