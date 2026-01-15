"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { ArrowUpDown, ArrowUp, ArrowDown, Download, Upload } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Sidebar } from "@/components/layout/sidebar";
import { PortfolioBalanceCard } from "@/components/dashboard/portfolio-balance-card";
import {
    getCashTransactions,
    createCashTransaction,
    deleteCashTransaction,
    updateCashTransaction,
    getPortfolioSummary,
    exportCash,
    importCash,
    CashTransaction,
    CashTransactionData,
    PortfolioSummary,
    ImportResult,
} from "@/services/api";
import { useCurrency } from "@/context/currency-context";

export default function AssetsPage() {
    const t = useTranslations("Assets");
    const tCommon = useTranslations("Common");
    const tTrades = useTranslations("Trades");
    const { formatMoney } = useCurrency();
    const { data: session, status } = useSession();
    const [transactions, setTransactions] = useState<CashTransaction[]>([]);
    const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [formData, setFormData] = useState<CashTransactionData>({
        date: new Date().toISOString().split("T")[0],
        type: "deposit",
        amount: 0,
        currency: "USD",
        notes: "",
    });
    const [selectedTransaction, setSelectedTransaction] = useState<CashTransaction | null>(null);
    const [isNotesDialogOpen, setIsNotesDialogOpen] = useState(false);
    const [editingNotes, setEditingNotes] = useState("");
    const [sortConfig, setSortConfig] = useState<{
        key: keyof CashTransaction | null;
        direction: "asc" | "desc";
    }>({ key: "date", direction: "desc" });
    const fileInputRef = useRef<HTMLInputElement>(null);

    const accessToken = (session as { accessToken?: string })?.accessToken;

    const fetchData = useCallback(async () => {
        if (!accessToken) return;
        try {
            const [txData, portfolioData] = await Promise.all([
                getCashTransactions(accessToken),
                getPortfolioSummary(accessToken),
            ]);
            setTransactions(txData.transactions);
            setPortfolio(portfolioData);
        } catch (error) {
            console.error("Failed to fetch data:", error);
        } finally {
            setIsLoading(false);
        }
    }, [accessToken]);

    useEffect(() => {
        if (accessToken) {
            fetchData();
        }
    }, [accessToken, fetchData]);

    if (status === "loading") {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-pulse text-muted-foreground">{tCommon("loading")}</div>
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
            await createCashTransaction(accessToken, {
                ...formData,
                date: new Date(formData.date).toISOString(),
            });
            setIsDialogOpen(false);
            setFormData({
                date: new Date().toISOString().split("T")[0],
                type: "deposit",
                amount: 0,
                currency: "USD",
                notes: "",
            });
            fetchData();
        } catch (error) {
            console.error("Failed to create transaction:", error);
        }
    };

    const handleDelete = async (id: string) => {
        if (!accessToken) return;
        try {
            await deleteCashTransaction(accessToken, id);
            fetchData();
        } catch (error) {
            console.error("Failed to delete transaction:", error);
        }
    };

    const handleViewNotes = (tx: CashTransaction) => {
        setSelectedTransaction(tx);
        setEditingNotes(tx.notes || "");
        setIsNotesDialogOpen(true);
    };

    const handleSaveNotes = async () => {
        if (!accessToken || !selectedTransaction) return;
        try {
            await updateCashTransaction(accessToken, selectedTransaction.id, { notes: editingNotes });
            setIsNotesDialogOpen(false);
            setSelectedTransaction(null);
            fetchData();
        } catch (error) {
            console.error("Failed to update notes:", error);
        }
    };
    const handleSort = (key: keyof CashTransaction) => {
        setSortConfig((current) => ({
            key,
            direction:
                current.key === key && current.direction === "asc" ? "desc" : "asc",
        }));
    };

    const sortedTransactions = [...transactions].sort((a, b) => {
        if (!sortConfig.key) return 0;

        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];

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
            const blob = await exportCash(accessToken, format);
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `cash_transactions.${format}`;
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
            const result = await importCash(accessToken, e.target.files[0]);
            if (result.success_count > 0) {
                alert(t('import_success', { count: result.success_count }));
                fetchData();
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

    // formatMoney is now provided by useCurrency()

    return (
        <div className="flex min-h-screen">
            <Sidebar accessToken={accessToken} />

            <main className="flex-1 p-6 overflow-auto">
                <div className="max-w-5xl mx-auto space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold">{t('title')}</h1>
                            <p className="text-muted-foreground">
                                {t('subtitle')}
                            </p>
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
                                    <Button>{t('add_transaction')}</Button>
                                </DialogTrigger>
                                <DialogContent>
                                    <DialogHeader>
                                        <DialogTitle>{t('add_cash_transaction')}</DialogTitle>
                                        <DialogDescription>
                                            {t('dialog_description')}
                                        </DialogDescription>
                                    </DialogHeader>
                                    <form onSubmit={handleSubmit} className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="type">{tTrades("type")}</Label>
                                                <select
                                                    id="type"
                                                    className="w-full h-10 px-3 border rounded-md bg-background"
                                                    value={formData.type}
                                                    onChange={(e) =>
                                                        setFormData({
                                                            ...formData,
                                                            type: e.target.value as "deposit" | "withdraw",
                                                        })
                                                    }
                                                >
                                                    <option value="deposit">{t('deposit')}</option>
                                                    <option value="withdraw">{t('withdraw')}</option>
                                                </select>
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="date">{tTrades("date")}</Label>
                                                <Input
                                                    id="date"
                                                    type="date"
                                                    value={formData.date}
                                                    onChange={(e) =>
                                                        setFormData({ ...formData, date: e.target.value })
                                                    }
                                                    required
                                                />
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <Label htmlFor="amount">{t('amount')}</Label>
                                                <Input
                                                    id="amount"
                                                    type="number"
                                                    step="0.01"
                                                    min="0"
                                                    value={formData.amount || ""}
                                                    onChange={(e) =>
                                                        setFormData({
                                                            ...formData,
                                                            amount: parseFloat(e.target.value) || 0,
                                                        })
                                                    }
                                                    required
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="currency">{tTrades("currency")}</Label>
                                                <select
                                                    id="currency"
                                                    className="w-full h-10 px-3 border rounded-md bg-background"
                                                    value={formData.currency}
                                                    onChange={(e) =>
                                                        setFormData({ ...formData, currency: e.target.value })
                                                    }
                                                >
                                                    <option value="USD">USD</option>
                                                    <option value="TWD">TWD</option>
                                                    <option value="EUR">EUR</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="notes">{t('notes_placeholder')}</Label>
                                            <Input
                                                id="notes"
                                                value={formData.notes || ""}
                                                onChange={(e) =>
                                                    setFormData({ ...formData, notes: e.target.value })
                                                }
                                                placeholder={t('notes_placeholder')}
                                            />
                                        </div>
                                        <div className="flex justify-end gap-2">
                                            <Button
                                                type="button"
                                                variant="outline"
                                                onClick={() => setIsDialogOpen(false)}
                                            >
                                                {t('cancel')}
                                            </Button>
                                            <Button type="submit">{t('add_transaction')}</Button>
                                        </div>
                                    </form>
                                </DialogContent>
                            </Dialog>
                        </div>
                    </div>

                    {/* Portfolio Balance Card */}
                    <PortfolioBalanceCard portfolio={portfolio} isLoading={isLoading} />

                    {/* Transactions Table */}
                    <Card>
                        <CardHeader>
                            <CardTitle>{t('history_title')}</CardTitle>
                            <CardDescription>{t('history_subtitle')}</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <div className="text-center py-8 text-muted-foreground">
                                    {tCommon("loading")}
                                </div>
                            ) : transactions.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">
                                    {t('no_transactions')}
                                </div>
                            ) : (
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>
                                                <Button
                                                    variant="ghost"
                                                    onClick={() => handleSort("date")}
                                                >
                                                    {tTrades("date")}
                                                    {sortConfig.key === "date" &&
                                                        (sortConfig.direction === "asc" ? (
                                                            <ArrowUp className="ml-2 h-4 w-4" />
                                                        ) : (
                                                            <ArrowDown className="ml-2 h-4 w-4" />
                                                        ))}
                                                    {sortConfig.key !== "date" && (
                                                        <ArrowUpDown className="ml-2 h-4 w-4" />
                                                    )}
                                                </Button>
                                            </TableHead>
                                            <TableHead>
                                                <Button
                                                    variant="ghost"
                                                    onClick={() => handleSort("type")}
                                                >
                                                    {tTrades("type")}
                                                    {sortConfig.key === "type" &&
                                                        (sortConfig.direction === "asc" ? (
                                                            <ArrowUp className="ml-2 h-4 w-4" />
                                                        ) : (
                                                            <ArrowDown className="ml-2 h-4 w-4" />
                                                        ))}
                                                    {sortConfig.key !== "type" && (
                                                        <ArrowUpDown className="ml-2 h-4 w-4" />
                                                    )}
                                                </Button>
                                            </TableHead>
                                            <TableHead className="text-right">
                                                <Button
                                                    variant="ghost"
                                                    onClick={() => handleSort("amount")}
                                                >
                                                    {t('amount')}
                                                    {sortConfig.key === "amount" &&
                                                        (sortConfig.direction === "asc" ? (
                                                            <ArrowUp className="ml-2 h-4 w-4" />
                                                        ) : (
                                                            <ArrowDown className="ml-2 h-4 w-4" />
                                                        ))}
                                                    {sortConfig.key !== "amount" && (
                                                        <ArrowUpDown className="ml-2 h-4 w-4" />
                                                    )}
                                                </Button>
                                            </TableHead>
                                            <TableHead>{tTrades("currency")}</TableHead>
                                            <TableHead></TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {sortedTransactions.map((tx) => (
                                            <TableRow
                                                key={tx.id}
                                                className="cursor-pointer hover:bg-muted/50"
                                                onClick={() => handleViewNotes(tx)}
                                            >
                                                <TableCell>
                                                    {new Date(tx.date).toLocaleDateString()}
                                                </TableCell>
                                                <TableCell>
                                                    <span
                                                        className={
                                                            tx.type === "deposit"
                                                                ? "text-green-600 dark:text-green-400"
                                                                : "text-red-600 dark:text-red-400"
                                                        }
                                                    >
                                                        {t(tx.type)}
                                                    </span>
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    {tx.type === "deposit" ? "+" : "-"}
                                                    {formatMoney(tx.amount)}
                                                </TableCell>
                                                <TableCell>{tx.currency}</TableCell>
                                                <TableCell>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="text-muted-foreground hover:text-destructive"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDelete(tx.id);
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
                </div>
            </main>

            {/* Notes View/Edit Dialog */}
            <Dialog open={isNotesDialogOpen} onOpenChange={setIsNotesDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>
                            {t('notes_dialog_title', { type: t(selectedTransaction?.type || 'deposit') })} ({formatMoney(selectedTransaction?.amount || 0)})
                        </DialogTitle>
                        <DialogDescription>
                            {selectedTransaction && new Date(selectedTransaction.date).toLocaleDateString()}
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
