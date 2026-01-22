"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { ArrowUpDown, ArrowUp, ArrowDown, Download, Upload } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
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
import { getTrades, createTrade, deleteTrade, updateTrade, getPortfolioSummary, exportTrades, importTrades, Trade, TradeData, PortfolioSummary, ImportResult } from "@/services/api";
import { PortfolioBalanceCard } from "@/components/dashboard/portfolio-balance-card";
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
        type: "buy",
        price: 0,
        quantity: 0,
        fees: 0,
        currency: "USD",
        notes: "",
    });
    const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
    const [isNotesDialogOpen, setIsNotesDialogOpen] = useState(false);
    const [editingNotes, setEditingNotes] = useState("");
    const [sortConfig, setSortConfig] = useState<{
        key: keyof Trade | "total_value" | null;
        direction: "asc" | "desc";
    }>({ key: "date", direction: "desc" });
    const fileInputRef = useRef<HTMLInputElement>(null);

    const accessToken = (session as { accessToken?: string })?.accessToken;

    const fetchTrades = useCallback(async () => {
        if (!accessToken) return;
        try {
            const [tradesData, portfolioData] = await Promise.all([
                getTrades(accessToken),
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
                type: "buy",
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

    const handleDelete = async (tradeId: string) => {
        if (!accessToken) return;
        if (!confirm("Are you sure you want to delete this trade?")) return;

        try {
            await deleteTrade(accessToken, tradeId);
            fetchTrades();
        } catch (error) {
            console.error("Failed to delete trade:", error);
        }
    };

    const handleViewNotes = (trade: Trade) => {
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
    const handleSort = (key: keyof Trade | "total_value") => {
        setSortConfig((current) => ({
            key,
            direction:
                current.key === key && current.direction === "asc" ? "desc" : "asc",
        }));
    };

    const sortedTrades = [...trades].sort((a, b) => {
        if (!sortConfig.key) return 0;

        let aValue: any = a[sortConfig.key as keyof Trade];
        let bValue: any = b[sortConfig.key as keyof Trade];

        if (sortConfig.key === "total_value") {
            aValue = Number(a.price) * Number(a.quantity);
            bValue = Number(b.price) * Number(b.quantity);
        }

        if (aValue === undefined || bValue === undefined) return 0;

        if (aValue < bValue) {
            return sortConfig.direction === "asc" ? -1 : 1;
        }
        if (aValue > bValue) {
            return sortConfig.direction === "asc" ? 1 : -1;
        }
        return 0;
    });

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

    const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!accessToken || !e.target.files?.[0]) return;
        try {
            const result = await importTrades(accessToken, e.target.files[0]);
            if (result.success_count > 0) {
                alert(t('import_success', { count: result.success_count }));
                fetchTrades();
            }
            if (result.error_count > 0) {
                alert(t('import_error', { count: result.error_count }));
            }
        } catch (error) {
            console.error("Import failed:", error);
        } finally {
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">{t('title')}</h1>
                    <p className="text-muted-foreground">{t('subtitle')}</p>
                </div>
                <div className="flex items-center gap-2">
                    {/* Export Dropdown */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="outline">
                                <Download className="h-4 w-4 mr-2" />
                                {t('export')}
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                            <DropdownMenuItem onClick={() => handleExport("csv")}>
                                {tCommon('csv')}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleExport("xlsx")}>
                                {tCommon('xlsx')}
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>

                    {/* Import Button */}
                    <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
                        <Upload className="h-4 w-4 mr-2" />
                        {t('import')}
                    </Button>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".csv,.xlsx"
                        className="hidden"
                        onChange={handleImport}
                    />

                    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                        <DialogTrigger asChild>
                            <Button>{t('add_trade')}</Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>{t('add_new_trade')}</DialogTitle>
                                <DialogDescription>
                                    {t('dialog_description')}
                                </DialogDescription>
                            </DialogHeader>
                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="symbol">{t('symbol')}</Label>
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
                                        <Label htmlFor="type">{t('type')}</Label>
                                        <select
                                            id="type"
                                            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs"
                                            value={formData.type}
                                            onChange={(e) =>
                                                setFormData({ ...formData, type: e.target.value as "buy" | "sell" })
                                            }
                                        >
                                            <option value="buy">{t('buy')}</option>
                                            <option value="sell">{t('sell')}</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="date">{t('date')}</Label>
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
                                        <Label htmlFor="price">{t('price')}</Label>
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
                                        <Label htmlFor="quantity">{t('quantity')}</Label>
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
                                        <Label htmlFor="fees">{t('fees')}</Label>
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
                                        <Label htmlFor="currency">{t('currency')}</Label>
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
                                    <Label htmlFor="notes">{t('notes')}</Label>
                                    <textarea
                                        id="notes"
                                        className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                                        placeholder={t('notes_placeholder')}
                                        value={formData.notes || ""}
                                        onChange={(e) =>
                                            setFormData({ ...formData, notes: e.target.value })
                                        }
                                    />
                                </div>
                                <Button type="submit" className="w-full">
                                    {t('add_trade')}
                                </Button>
                            </form>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            {/* Portfolio Balance Card */}
            <PortfolioBalanceCard portfolio={portfolio} isLoading={isLoading} />

            <Card>
                <CardHeader>
                    <CardTitle>{t('history_title')}</CardTitle>
                </CardHeader>
                <CardContent>
                    {trades.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            {t('no_trades')}
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>
                                        <Button variant="ghost" onClick={() => handleSort("date")}>
                                            {t('date')}
                                            {sortConfig.key === "date" ? (
                                                sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                            ) : (
                                                <ArrowUpDown className="ml-2 h-4 w-4" />
                                            )}
                                        </Button>
                                    </TableHead>
                                    <TableHead>
                                        <Button variant="ghost" onClick={() => handleSort("symbol")}>
                                            {t('symbol')}
                                            {sortConfig.key === "symbol" ? (
                                                sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                            ) : (
                                                <ArrowUpDown className="ml-2 h-4 w-4" />
                                            )}
                                        </Button>
                                    </TableHead>
                                    <TableHead>
                                        <Button variant="ghost" onClick={() => handleSort("type")}>
                                            {t('type')}
                                            {sortConfig.key === "type" ? (
                                                sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                            ) : (
                                                <ArrowUpDown className="ml-2 h-4 w-4" />
                                            )}
                                        </Button>
                                    </TableHead>
                                    <TableHead className="text-right">
                                        <Button variant="ghost" onClick={() => handleSort("price")}>
                                            {t('price')}
                                            {sortConfig.key === "price" ? (
                                                sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                            ) : (
                                                <ArrowUpDown className="ml-2 h-4 w-4" />
                                            )}
                                        </Button>
                                    </TableHead>
                                    <TableHead className="text-right">
                                        <Button variant="ghost" onClick={() => handleSort("quantity")}>
                                            {t('quantity')}
                                            {sortConfig.key === "quantity" ? (
                                                sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                            ) : (
                                                <ArrowUpDown className="ml-2 h-4 w-4" />
                                            )}
                                        </Button>
                                    </TableHead>
                                    <TableHead className="text-right">
                                        <Button variant="ghost" onClick={() => handleSort("total_value")}>
                                            {t('total')}
                                            {sortConfig.key === "total_value" ? (
                                                sortConfig.direction === "asc" ? <ArrowUp className="ml-2 h-4 w-4" /> : <ArrowDown className="ml-2 h-4 w-4" />
                                            ) : (
                                                <ArrowUpDown className="ml-2 h-4 w-4" />
                                            )}
                                        </Button>
                                    </TableHead>
                                    <TableHead></TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {sortedTrades.map((trade) => (
                                    <TableRow
                                        key={trade.id}
                                        className="cursor-pointer hover:bg-muted/50"
                                        onClick={() => handleViewNotes(trade)}
                                    >
                                        <TableCell>
                                            {new Date(trade.date).toLocaleDateString()}
                                        </TableCell>
                                        <TableCell className="font-medium">{trade.symbol}</TableCell>
                                        <TableCell>
                                            <span
                                                className={
                                                    trade.type === "buy"
                                                        ? "text-green-600 dark:text-green-400"
                                                        : "text-red-600 dark:text-red-400"
                                                }
                                            >
                                                {t(trade.type)}
                                            </span>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            {formatMoney(Number(trade.price))}
                                        </TableCell>
                                        <TableCell className="text-right">{Number(trade.quantity)}</TableCell>
                                        <TableCell className="text-right">
                                            {formatMoney(Number(trade.price) * Number(trade.quantity))}
                                        </TableCell>
                                        <TableCell>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDelete(trade.id);
                                                }}
                                            >
                                                {t('delete')}
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>

            {/* Notes View/Edit Dialog */}
            <Dialog open={isNotesDialogOpen} onOpenChange={setIsNotesDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>
                            {t('notes_dialog_title', { symbol: selectedTrade?.symbol || '' })} ({t(selectedTrade?.type || 'buy')})
                        </DialogTitle>
                        <DialogDescription>
                            {selectedTrade && new Date(selectedTrade.date).toLocaleDateString()} •
                            {selectedTrade && ` ${formatMoney(Number(selectedTrade.price) * Number(selectedTrade.quantity))}`}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <textarea
                            className="flex min-h-[150px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            placeholder={t('notes_placeholder')}
                            value={editingNotes}
                            onChange={(e) => setEditingNotes(e.target.value)}
                        />
                        <div className="flex gap-2 justify-end">
                            <Button variant="outline" onClick={() => setIsNotesDialogOpen(false)}>
                                {t('cancel')}
                            </Button>
                            <Button onClick={handleSaveNotes}>
                                {t('save_notes')}
                            </Button>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
}

