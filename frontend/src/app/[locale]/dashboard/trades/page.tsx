"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";
import { useTranslations } from "next-intl";
import { ColumnDef } from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import { Download, Upload } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { getTrades, createTrade, deleteTrade, updateTrade, getPortfolioSummary, exportTrades, Trade, TradeData, PortfolioSummary } from "@/services/api";
import { PortfolioBalanceCard } from "@/components/dashboard/portfolio-balance-card";
import { TransactionImportDialog } from "@/components/portfolio/transaction-import-dialog";
import { DataTable, DataTableSearch } from "@/components/ui/data-table";
import { DataTableColumnHeader } from "@/components/ui/data-table-column-header";
import { useCurrency } from "@/context/currency-context";
import { Loader2 } from "lucide-react";

export default function TradesPage() {
    const t = useTranslations("Trades");
    const tCommon = useTranslations("Common");
    const { formatMoney } = useCurrency();
    const { data: session, status } = useSession();
    const [trades, setTrades] = useState<Trade[]>([]);
    const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [formData, setFormData] = useState<TradeData>({
        symbol: "",
        date: new Date().toISOString().split("T")[0],
        action: "Buy",
        price: 0,
        quantity: 0,
        fees: 0,
        currency: "USD",
        notes: "",
    });
    const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
    const [isNotesDialogOpen, setIsNotesDialogOpen] = useState(false);
    const [editingNotes, setEditingNotes] = useState("");
    const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");

    const accessToken = (session as { accessToken?: string })?.accessToken;

    const fetchTrades = useCallback(async () => {
        if (!accessToken) return;
        try {
            // Fetch all trades for client-side sorting/filtering
            const [tradesData, portfolioData] = await Promise.all([
                getTrades(accessToken, 0, 10000),
                getPortfolioSummary(accessToken),
            ]);
            setTrades(tradesData.trades);
            setPortfolio(portfolioData);
        } catch (error) {
            console.error("Failed to fetch trades:", error);
        } finally {
            setIsLoading(false);
        }
    }, [accessToken]);

    useEffect(() => {
        if (accessToken) {
            fetchTrades();
        }
    }, [accessToken, fetchTrades]);

    // Define handleDelete before columns useMemo
    const handleDelete = useCallback(async (tradeId: string) => {
        if (!accessToken) return;
        if (!confirm("Are you sure you want to delete this trade?")) return;

        try {
            await deleteTrade(accessToken, tradeId);
            fetchTrades();
        } catch (error) {
            console.error("Failed to delete trade:", error);
        }
    }, [accessToken, fetchTrades]);

    // Define columns for DataTable
    const columns: ColumnDef<Trade>[] = useMemo(() => [
        {
            accessorKey: "date",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("date")} className="w-full justify-center" />
            ),
            cell: ({ row }) => <div className="text-center">{new Date(row.getValue("date")).toLocaleDateString()}</div>,
            sortingFn: "datetime",
        },
        {
            accessorKey: "symbol",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("symbol")} className="w-full justify-center" />
            ),
            cell: ({ row }) => <div className="text-center font-medium">{row.getValue("symbol")}</div>,
        },
        {
            accessorKey: "action",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("action")} className="w-full justify-center" />
            ),
            cell: ({ row }) => {
                // Color based on amount sign: negative = red (cash outflow), positive = green (cash inflow)
                // If amount is null, no color
                const amount = row.original.amount;
                const isNegative = amount != null && amount < 0;
                const isPositive = amount != null && amount > 0;
                return (
                    <div className="text-center">
                        <span className={
                            isNegative ? "text-red-600 dark:text-red-400" :
                            isPositive ? "text-green-600 dark:text-green-400" :
                            ""
                        }>
                            {row.getValue("action")}
                        </span>
                    </div>
                );
            },
        },
        {
            accessorKey: "price",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("price")} className="w-full justify-center" />
            ),
            cell: ({ row }) => <div className="text-center">{formatMoney(Number(row.getValue("price")))}</div>,
        },
        {
            accessorKey: "quantity",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("quantity")} className="w-full justify-center" />
            ),
            cell: ({ row }) => <div className="text-center">{Number(row.getValue("quantity"))}</div>,
        },
        {
            id: "amount",
            accessorFn: (row) => {
                // Use original amount if available, otherwise calculate from price * quantity
                if (row.amount != null) {
                    return row.amount;
                }
                return Number(row.price) * Number(row.quantity);
            },
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("amount")} className="w-full justify-center" />
            ),
            cell: ({ row }) => {
                const originalAmount = row.original.amount;
                const total = Number(row.original.price) * Number(row.original.quantity);
                // Use original amount if available, otherwise just show total without color
                const displayAmount = originalAmount != null ? originalAmount : total;
                const isNegative = originalAmount != null && originalAmount < 0;
                const isPositive = originalAmount != null && originalAmount > 0;
                return (
                    <div className={`text-center ${
                        isNegative ? "text-red-600 dark:text-red-400" :
                        isPositive ? "text-green-600 dark:text-green-400" :
                        ""
                    }`}>
                        {formatMoney(displayAmount)}
                    </div>
                );
            },
        },
        {
            id: "actions",
            header: () => <div className="text-center w-full"> </div>,
            cell: ({ row }) => (
                <div className="text-center">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                        onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(row.original.id);
                        }}
                    >
                        {t("delete")}
                    </Button>
                </div>
            ),
        },
    ], [t, formatMoney, handleDelete]);

    if (status === "loading" || isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (!session) {
        redirect("/login");
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!accessToken) return;

        try {
            await createTrade(accessToken, {
                ...formData,
                date: new Date(formData.date).toISOString(),
            });
            setIsDialogOpen(false);
            setFormData({
                symbol: "",
                date: new Date().toISOString().split("T")[0],
                action: "Buy",
                price: 0,
                quantity: 0,
                fees: 0,
                currency: "USD",
                notes: "",
            });
            fetchTrades();
        } catch (error) {
            console.error("Failed to create trade:", error);
        }
    };

    const handleRowClick = (trade: Trade) => {
        setSelectedTrade(trade);
        setEditingNotes(trade.notes || "");
        setIsNotesDialogOpen(true);
    };

    const handleSaveNotes = async () => {
        if (!accessToken || !selectedTrade) return;
        try {
            await updateTrade(accessToken, selectedTrade.id, { notes: editingNotes });
            setIsNotesDialogOpen(false);
            setSelectedTrade(null);
            fetchTrades();
        } catch (error) {
            console.error("Failed to update notes:", error);
        }
    };

    const handleExport = async (format: "csv" | "xlsx") => {
        if (!accessToken) return;
        try {
            const blob = await exportTrades(accessToken, format);
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `trades.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Export failed:", error);
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">{t("title")}</h1>
                    <p className="text-muted-foreground">{t("subtitle")}</p>
                </div>
                <div className="flex items-center gap-2">
                    {/* Export Dropdown */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline">
                                <Download className="h-4 w-4 mr-2" />
                                {t("export")}
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                            <DropdownMenuItem onClick={() => handleExport("csv")}>
                                {tCommon("csv")}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleExport("xlsx")}>
                                {tCommon("xlsx")}
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>

                    {/* Import Button - uses unified importer */}
                    <Button variant="outline" onClick={() => setIsImportDialogOpen(true)}>
                        <Upload className="h-4 w-4 mr-2" />
                        {t("import")}
                    </Button>

                    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                        <DialogTrigger asChild>
                            <Button>{t("add_trade")}</Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>{t("add_new_trade")}</DialogTitle>
                                <DialogDescription>{t("dialog_description")}</DialogDescription>
                            </DialogHeader>
                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="symbol">{t("symbol")}</Label>
                                        <Input
                                            id="symbol"
                                            placeholder="AAPL"
                                            value={formData.symbol}
                                            onChange={(e) =>
                                                setFormData({ ...formData, symbol: e.target.value.toUpperCase() })
                                            }
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="action">{t("action")}</Label>
                                        <select
                                            id="action"
                                            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs"
                                            value={formData.action}
                                            onChange={(e) =>
                                                setFormData({ ...formData, action: e.target.value })
                                            }
                                        >
                                            <option value="Buy">{t("buy")}</option>
                                            <option value="Sell">{t("sell")}</option>
                                            <option value="Reinvest">{t("reinvest")}</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="date">{t("date")}</Label>
                                    <Input
                                        id="date"
                                        type="date"
                                        value={formData.date}
                                        onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                                        required
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="price">{t("price")}</Label>
                                        <Input
                                            id="price"
                                            type="number"
                                            step="0.01"
                                            min="0.01"
                                            placeholder="150.00"
                                            value={formData.price || ""}
                                            onChange={(e) =>
                                                setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })
                                            }
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="quantity">{t("quantity")}</Label>
                                        <Input
                                            id="quantity"
                                            type="number"
                                            step="0.000001"
                                            min="0.000001"
                                            placeholder="10"
                                            value={formData.quantity || ""}
                                            onChange={(e) =>
                                                setFormData({ ...formData, quantity: parseFloat(e.target.value) || 0 })
                                            }
                                            required
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="fees">{t("fees")}</Label>
                                        <Input
                                            id="fees"
                                            type="number"
                                            step="0.01"
                                            min="0"
                                            placeholder="0.00"
                                            value={formData.fees || ""}
                                            onChange={(e) =>
                                                setFormData({ ...formData, fees: parseFloat(e.target.value) || 0 })
                                            }
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="currency">{t("currency")}</Label>
                                        <Input
                                            id="currency"
                                            placeholder="USD"
                                            value={formData.currency}
                                            onChange={(e) =>
                                                setFormData({ ...formData, currency: e.target.value.toUpperCase() })
                                            }
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="notes">{t("notes")}</Label>
                                    <textarea
                                        id="notes"
                                        className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                                        placeholder={t("notes_placeholder")}
                                        value={formData.notes || ""}
                                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                    />
                                </div>
                                <Button type="submit" className="w-full">
                                    {t("add_trade")}
                                </Button>
                            </form>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            {/* Portfolio Balance Card */}
            <PortfolioBalanceCard portfolio={portfolio} isLoading={isLoading} />

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                    <CardTitle>{t("history_title")}</CardTitle>
                    <DataTableSearch
                        value={searchQuery}
                        onChange={setSearchQuery}
                        placeholder={t("search_placeholder")}
                    />
                </CardHeader>
                <CardContent>
                    <DataTable
                        columns={columns}
                        data={trades}
                        onRowClick={handleRowClick}
                        externalSearch={searchQuery}
                        onExternalSearchChange={setSearchQuery}
                        centered={true}
                    />
                </CardContent>
            </Card>

            {/* Notes View/Edit Dialog */}
            <Dialog open={isNotesDialogOpen} onOpenChange={setIsNotesDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>
                            {t("notes_dialog_title", { symbol: selectedTrade?.symbol || "" })} (
                            {selectedTrade?.action || "Buy"})
                        </DialogTitle>
                        <DialogDescription>
                            {selectedTrade && new Date(selectedTrade.date).toLocaleDateString()} •
                            {selectedTrade &&
                                ` ${formatMoney(Number(selectedTrade.price) * Number(selectedTrade.quantity))}`}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <textarea
                            className="flex min-h-[150px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            placeholder={t("notes_placeholder")}
                            value={editingNotes}
                            onChange={(e) => setEditingNotes(e.target.value)}
                        />
                        <div className="flex gap-2 justify-end">
                            <Button variant="outline" onClick={() => setIsNotesDialogOpen(false)}>
                                {t("cancel")}
                            </Button>
                            <Button onClick={handleSaveNotes}>{t("save_notes")}</Button>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>

            {/* Brokerage Import Dialog */}
            <TransactionImportDialog
                open={isImportDialogOpen}
                onOpenChange={setIsImportDialogOpen}
                onSuccess={fetchTrades}
            />
        </div>
    );
}
