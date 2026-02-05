"use client";

import { useState, useEffect, useCallback } from "react";
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
import { PortfolioBalanceCard } from "@/components/dashboard/portfolio-balance-card";
import { TransactionImportDialog } from "@/components/portfolio/transaction-import-dialog";
import { DataTable, DataTableSearch } from "@/components/ui/data-table";
import { DataTableColumnHeader } from "@/components/ui/data-table-column-header";
import {
    getCashTransactions,
    createCashTransaction,
    deleteCashTransaction,
    updateCashTransaction,
    getPortfolioSummary,
    exportCash,
    CashTransaction,
    CashTransactionData,
    PortfolioSummary,
} from "@/services/api";
import { useCurrency } from "@/context/currency-context";
import { Loader2 } from "lucide-react";

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
        action: "Deposit",
        amount: 0,
        currency: "USD",
        notes: "",
    });
    const [selectedTransaction, setSelectedTransaction] = useState<CashTransaction | null>(null);
    const [isNotesDialogOpen, setIsNotesDialogOpen] = useState(false);
    const [editingNotes, setEditingNotes] = useState("");
    const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");

    const accessToken = (session as { accessToken?: string })?.accessToken;

    const fetchData = useCallback(async () => {
        if (!accessToken) return;
        try {
            const [txData, portfolioData] = await Promise.all([
                getCashTransactions(accessToken, 0, 10000),
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
            await createCashTransaction(accessToken, {
                ...formData,
                date: new Date(formData.date).toISOString(),
            });
            setIsDialogOpen(false);
            setFormData({
                date: new Date().toISOString().split("T")[0],
                action: "Deposit",
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
        if (!confirm("Are you sure you want to delete this transaction?")) return;

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

    // Define columns for DataTable
    const columns: ColumnDef<CashTransaction>[] = [
        {
            accessorKey: "date",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={tTrades("date")} className="w-full justify-center" />
            ),
            cell: ({ row }) => <div className="text-center">{new Date(row.getValue("date")).toLocaleDateString()}</div>,
        },
        {
            accessorKey: "action",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("action")} className="w-full justify-center" />
            ),
            cell: ({ row }) => {
                // Color based on amount sign: positive = green (inflow), negative = red (outflow)
                const amount = row.original.amount as number;
                const isPositive = amount > 0;
                const isNegative = amount < 0;
                return (
                    <div className="text-center">
                        <span className={
                            isPositive ? "text-green-600 dark:text-green-400" :
                            isNegative ? "text-red-600 dark:text-red-400" :
                            ""
                        }>
                            {row.getValue("action")}
                        </span>
                    </div>
                );
            },
        },
        {
            accessorKey: "amount",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={t("amount")} className="w-full justify-center" />
            ),
            cell: ({ row }) => {
                const amount = row.getValue("amount") as number;
                const isPositive = amount > 0;
                const isNegative = amount < 0;
                return (
                    <div className={`text-center ${
                        isPositive ? "text-green-600 dark:text-green-400" :
                        isNegative ? "text-red-600 dark:text-red-400" :
                        ""
                    }`}>
                        {formatMoney(amount)}
                    </div>
                );
            },
        },
        {
            accessorKey: "currency",
            header: ({ column }) => (
                <DataTableColumnHeader column={column} title={tTrades("currency")} className="w-full justify-center" />
            ),
            cell: ({ row }) => <div className="text-center">{row.getValue("currency")}</div>,
        },
        {
            id: "actions",
            header: () => <div className="text-center w-full"> </div>,
            cell: ({ row }) => (
                <div className="text-center">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="text-muted-foreground hover:text-destructive"
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
    ];

    return (
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

                    {/* Import Button - uses unified importer */}
                    <Button variant="outline" onClick={() => setIsImportDialogOpen(true)}>
                        <Upload className="h-4 w-4 mr-2" />
                        {t('import')}
                    </Button>

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
                                    <div className="space-y-2">
                                        <Label htmlFor="action">{t("action")}</Label>
                                        <select
                                            id="action"
                                            className="w-full h-10 px-3 border rounded-md bg-background"
                                            value={formData.action}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    action: e.target.value,
                                                })
                                            }
                                        >
                                            <option value="Deposit">{t('deposit')}</option>
                                            <option value="Withdraw">{t('withdraw')}</option>
                                            <option value="Dividend">{t('dividend')}</option>
                                            <option value="Tax">{t('tax')}</option>
                                            <option value="Interest">{t('interest')}</option>
                                            <option value="Fee">{t('fee')}</option>
                                        </select>
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
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                    <CardTitle>{t('history_title')}</CardTitle>
                    <DataTableSearch
                        value={searchQuery}
                        onChange={setSearchQuery}
                        placeholder={t("search_placeholder")}
                    />
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="text-center py-8 text-muted-foreground">
                            {tCommon("loading")}
                        </div>
                    ) : (
                        <DataTable
                            columns={columns}
                            data={transactions}
                            onRowClick={handleViewNotes}
                            externalSearch={searchQuery}
                            onExternalSearchChange={setSearchQuery}
                            centered={true}
                        />
                    )}
                </CardContent>
            </Card>

            {/* Notes View/Edit Dialog */}
            <Dialog open={isNotesDialogOpen} onOpenChange={setIsNotesDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>
                            {t('notes_dialog_title', { type: selectedTransaction?.action || 'Deposit' })} ({formatMoney(selectedTransaction?.amount || 0)})
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

            {/* Import Dialog */}
            <TransactionImportDialog
                open={isImportDialogOpen}
                onOpenChange={setIsImportDialogOpen}
                onSuccess={fetchData}
            />
        </div>
    );
}
