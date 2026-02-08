"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";
import { useTranslations } from "next-intl";
import { ColumnDef } from "@tanstack/react-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { KPICards } from "@/components/dashboard/kpi-cards";
import { OverviewCharts } from "@/components/dashboard/overview-charts";
import { DataTable, DataTableSearch } from "@/components/ui/data-table";
import { DataTableColumnHeader } from "@/components/ui/data-table-column-header";
import { Loader2 } from "lucide-react";
import { getPortfolioSummary, PortfolioSummary, Holding } from "@/services/api";
import { useCurrency } from "@/context/currency-context";

export default function DashboardPage() {
    const t = useTranslations("Dashboard");
    const { formatMoney } = useCurrency();
    const { data: session, status } = useSession();
    const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");

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

    const formatPercent = (value: number) => {
        const sign = value >= 0 ? "+" : "";
        return `${sign}${value.toFixed(2)}%`;
    };

    // Define columns for Holdings DataTable
    const columns: ColumnDef<Holding>[] = [
        {
            accessorKey: "symbol",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("table_symbol")} className="w-full justify-center" />
            ),
            cell: ({ row }) => (
                <div className="text-center font-medium">{row.getValue("symbol")}</div>
            ),
        },
        {
            accessorKey: "quantity",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("table_quantity")} className="w-full justify-center" />
            ),
            cell: ({ row }) => (
                <div className="text-center">{(row.getValue("quantity") as number).toFixed(2)}</div>
            ),
        },
        {
            accessorKey: "avg_cost",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("table_avg_cost")} className="w-full justify-center" />
            ),
            cell: ({ row }) => (
                <div className="text-center">{formatMoney(row.getValue("avg_cost") as number)}</div>
            ),
        },
        {
            accessorKey: "current_price",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("table_price")} className="w-full justify-center" />
            ),
            cell: ({ row }) => {
                const price = row.getValue("current_price") as number | null;
                return (
                    <div className="text-center">{price ? formatMoney(price) : "N/A"}</div>
                );
            },
        },
        {
            accessorKey: "current_value",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("table_value")} className="w-full justify-center" />
            ),
            cell: ({ row }) => (
                <div className="text-center">{formatMoney(row.getValue("current_value") as number)}</div>
            ),
        },
        {
            accessorKey: "unrealized_pnl",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("table_pnl")} className="w-full justify-center" />
            ),
            cell: ({ row }) => {
                const pnl = row.getValue("unrealized_pnl") as number;
                const pnlPercent = row.original.unrealized_pnl_percent;
                return (
                    <div className={`text-center ${pnl >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>
                        {formatMoney(pnl)}
                        <span className="text-xs ml-1">({formatPercent(pnlPercent)})</span>
                    </div>
                );
            },
        },
        {
            accessorKey: "price_change_percent",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("table_change")} className="w-full justify-center" />
            ),
            cell: ({ row }) => {
                const change = row.original.price_change || 0;
                const changePercent = row.getValue("price_change_percent") as number | null;
                return (
                    <div className={`text-center ${change >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>
                        {changePercent !== null ? formatPercent(changePercent) : "N/A"}
                    </div>
                );
            },
        },
    ];

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold">{t('title')}</h1>
                    <p className="text-muted-foreground">{t('welcome_back', { email: session.user?.email || '' })}</p>
                </div>
                <Button onClick={fetchPortfolio} variant="outline" size="sm" className="self-start sm:self-auto">
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
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                            <CardTitle>{t('holdings_title')}</CardTitle>
                            <DataTableSearch
                                value={searchQuery}
                                onChange={setSearchQuery}
                                placeholder={t("table_symbol")}
                            />
                        </CardHeader>
                        <CardContent>
                            {!portfolio?.holdings || portfolio.holdings.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">
                                    {t('no_holdings')}
                                </div>
                            ) : (
                                <DataTable
                                    columns={columns}
                                    data={portfolio.holdings}
                                    externalSearch={searchQuery}
                                    onExternalSearchChange={setSearchQuery}
                                    centered={true}
                                />
                            )}
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    );
}
