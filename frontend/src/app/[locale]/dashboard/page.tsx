"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { KPICards } from "@/components/dashboard/kpi-cards";
import { OverviewCharts } from "@/components/dashboard/overview-charts";
import { ArrowUpDown, ArrowUp, ArrowDown, Loader2 } from "lucide-react";
import { getPortfolioSummary, PortfolioSummary, Holding } from "@/services/api";
import { useCurrency } from "@/context/currency-context";

export default function DashboardPage() {
    const t = useTranslations("Dashboard");
    const tCommon = useTranslations("Common");
    const { formatMoney } = useCurrency();
    const { data: session, status } = useSession();
    const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [sortConfig, setSortConfig] = useState<{
        key: keyof Holding | null;
        direction: "asc" | "desc";
    }>({ key: "current_value", direction: "desc" });

    const accessToken = (session as { accessToken?: string })?.accessToken;

    const fetchPortfolio = useCallback(async () => {
        if (!accessToken) return;
        setError(null);
        try {
            const data = await getPortfolioSummary(accessToken);
            setPortfolio(data);
        } catch (err) {
            setError("Failed to load portfolio data");
            console.error("Portfolio fetch error:", err);
        } finally {
            setIsLoading(false);
        }
    }, [accessToken]);

    useEffect(() => {
        if (accessToken) {
            fetchPortfolio();
        }
    }, [accessToken, fetchPortfolio]);

    if (status === "loading") {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (!session) {
        redirect("/login");
    }

    // formatMoney is now provided by useCurrency()

    const formatPercent = (value: number) => {
        const sign = value >= 0 ? "+" : "";
        return `${sign}${value.toFixed(2)}%`;
    };

    const handleSort = (key: keyof Holding) => {
        setSortConfig((current) => ({
            key,
            direction:
                current.key === key && current.direction === "asc" ? "desc" : "asc",
        }));
    };

    const sortedHoldings = [...(portfolio?.holdings || [])].sort((a, b) => {
        if (!sortConfig.key) return 0;

        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];

        if (aValue === null && bValue === null) return 0;
        if (aValue === null) return 1;
        if (bValue === null) return -1;

        if (aValue < bValue!) {
            return sortConfig.direction === "asc" ? -1 : 1;
        }
        if (aValue > bValue!) {
            return sortConfig.direction === "asc" ? 1 : -1;
        }
        return 0;
    });

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">{t('title')}</h1>
                    <p className="text-muted-foreground">{t('welcome_back', { email: session.user?.email || '' })}</p>
                </div>
                <Button onClick={fetchPortfolio} variant="outline" size="sm">
                    {t('refresh')}
                </Button>
            </div>

            {error && (
                <Card className="border-destructive">
                    <CardContent className="py-4 text-destructive">{error}</CardContent>
                </Card>
            )}

            {isLoading ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    {[...Array(4)].map((_, i) => (
                        <Card key={i}>
                            <CardHeader className="pb-2">
                                <div className="h-4 w-24 bg-muted animate-pulse rounded" />
                                <div className="h-8 w-32 bg-muted animate-pulse rounded mt-2" />
                            </CardHeader>
                        </Card>
                    ))}
                </div>
            ) : (
                <>
                    {/* KPI Cards */}
                    <KPICards portfolio={portfolio} />

                    {/* Charts */}
                    <OverviewCharts holdings={portfolio?.holdings || []} />

                    {/* Holdings Table */}
                    <Card>
                        <CardHeader>
                            <CardTitle>{t('holdings_title')}</CardTitle>
                            <CardDescription>{t('holdings_subtitle')}</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {!portfolio?.holdings || portfolio.holdings.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">
                                    {t('no_holdings')}
                                </div>
                            ) : (
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>
                                                <Button variant="ghost" onClick={() => handleSort("symbol")}>
                                                    {t('table_symbol')}
                                                    {sortConfig.key === "symbol" ? (
                                                        sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                                    ) : (
                                                        <ArrowUpDown className="ml-2 h-4 w-4" />
                                                    )}
                                                </Button>
                                            </TableHead>
                                            <TableHead className="text-right">
                                                <Button variant="ghost" onClick={() => handleSort("quantity")}>
                                                    {t('table_quantity')}
                                                    {sortConfig.key === "quantity" ? (
                                                        sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                                    ) : (
                                                        <ArrowUpDown className="ml-2 h-4 w-4" />
                                                    )}
                                                </Button>
                                            </TableHead>
                                            <TableHead className="text-right">
                                                <Button variant="ghost" onClick={() => handleSort("avg_cost")}>
                                                    {t('table_avg_cost')}
                                                    {sortConfig.key === "avg_cost" ? (
                                                        sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                                    ) : (
                                                        <ArrowUpDown className="ml-2 h-4 w-4" />
                                                    )}
                                                </Button>
                                            </TableHead>
                                            <TableHead className="text-right">
                                                <Button variant="ghost" onClick={() => handleSort("current_price")}>
                                                    {t('table_price')}
                                                    {sortConfig.key === "current_price" ? (
                                                        sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                                    ) : (
                                                        <ArrowUpDown className="ml-2 h-4 w-4" />
                                                    )}
                                                </Button>
                                            </TableHead>
                                            <TableHead className="text-right">
                                                <Button variant="ghost" onClick={() => handleSort("current_value")}>
                                                    {t('table_value')}
                                                    {sortConfig.key === "current_value" ? (
                                                        sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                                    ) : (
                                                        <ArrowUpDown className="ml-2 h-4 w-4" />
                                                    )}
                                                </Button>
                                            </TableHead>
                                            <TableHead className="text-right">
                                                <Button variant="ghost" onClick={() => handleSort("unrealized_pnl")}>
                                                    {t('table_pnl')}
                                                    {sortConfig.key === "unrealized_pnl" ? (
                                                        sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                                    ) : (
                                                        <ArrowUpDown className="ml-2 h-4 w-4" />
                                                    )}
                                                </Button>
                                            </TableHead>
                                            <TableHead className="text-right">
                                                <Button variant="ghost" onClick={() => handleSort("price_change_percent")}>
                                                    {t('table_change')}
                                                    {sortConfig.key === "price_change_percent" ? (
                                                        sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                                    ) : (
                                                        <ArrowUpDown className="ml-2 h-4 w-4" />
                                                    )}
                                                </Button>
                                            </TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {sortedHoldings.map((holding) => (
                                            <TableRow key={holding.symbol}>
                                                <TableCell className="font-medium">{holding.symbol}</TableCell>
                                                <TableCell className="text-right">
                                                    {holding.quantity.toFixed(2)}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    {formatMoney(holding.avg_cost)}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    {holding.current_price
                                                        ? formatMoney(holding.current_price)
                                                        : "N/A"}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    {formatMoney(holding.current_value)}
                                                </TableCell>
                                                <TableCell
                                                    className={`text-right ${holding.unrealized_pnl >= 0
                                                        ? "text-green-600 dark:text-green-400"
                                                        : "text-red-600 dark:text-red-400"
                                                        }`}
                                                >
                                                    {formatMoney(holding.unrealized_pnl)}
                                                    <span className="text-xs ml-1">
                                                        ({formatPercent(holding.unrealized_pnl_percent)})
                                                    </span>
                                                </TableCell>
                                                <TableCell
                                                    className={`text-right ${(holding.price_change || 0) >= 0
                                                        ? "text-green-600 dark:text-green-400"
                                                        : "text-red-600 dark:text-red-400"
                                                        }`}
                                                >
                                                    {holding.price_change_percent !== null
                                                        ? formatPercent(holding.price_change_percent)
                                                        : "N/A"}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            )}
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    );
}
