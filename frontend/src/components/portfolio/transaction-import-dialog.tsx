"use client";

import { useState, useRef } from "react";
import { useSession } from "next-auth/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Upload, Loader2, AlertCircle, CheckCircle2, FileWarning } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { uploadBrokerageFile, ImporterResult } from "@/services/api";

interface TransactionImportDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess?: () => void;
}

export function TransactionImportDialog({
    open,
    onOpenChange,
    onSuccess,
}: TransactionImportDialogProps) {
    const { data: session } = useSession();
    const t = useTranslations("Import");
    const queryClient = useQueryClient();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [result, setResult] = useState<ImporterResult | null>(null);

    const accessToken = (session as { accessToken?: string })?.accessToken;

    const uploadMutation = useMutation({
        mutationFn: async () => {
            if (!accessToken || !selectedFile) {
                throw new Error("Missing access token or file");
            }
            return uploadBrokerageFile(accessToken, selectedFile);
        },
        onSuccess: (data) => {
            setResult(data);
            queryClient.invalidateQueries({ queryKey: ["trades"] });
            queryClient.invalidateQueries({ queryKey: ["portfolio"] });
            queryClient.invalidateQueries({ queryKey: ["cash-transactions"] });
            if (onSuccess) {
                onSuccess();
            }
        },
    });

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            setResult(null);
        }
    };

    const handleUpload = () => {
        uploadMutation.mutate();
    };

    const handleClose = () => {
        setSelectedFile(null);
        setResult(null);
        onOpenChange(false);
    };

    const handleSelectFile = () => {
        fileInputRef.current?.click();
    };

    return (
        <Dialog open={open} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>{t("import_brokerage_title")}</DialogTitle>
                    <DialogDescription>
                        {t("import_brokerage_description")}
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                    {/* File Selection - Hide when result exists */}
                    {!result && (
                        <div className="border-2 border-dashed rounded-lg p-6 text-center">
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".csv,.xlsx,.xls"
                                className="hidden"
                                onChange={handleFileChange}
                            />
                            {selectedFile ? (
                                <div className="space-y-2">
                                    <div className="flex items-center justify-center gap-2 text-sm">
                                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                                        <span className="font-medium">{selectedFile.name}</span>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={handleSelectFile}
                                        disabled={uploadMutation.isPending}
                                    >
                                        {t("change_file")}
                                    </Button>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    <Upload className="h-10 w-10 mx-auto text-muted-foreground" />
                                    <div>
                                        <Button
                                            variant="outline"
                                            onClick={handleSelectFile}
                                        >
                                            {t("select_file")}
                                        </Button>
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        {t("supported_formats")}
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Upload Result */}
                    {result && (
                        <div className="rounded-lg border p-4 space-y-3">
                            <div className="flex items-center gap-2">
                                {result.errors.length === 0 ? (
                                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                                ) : (
                                    <AlertCircle className="h-5 w-5 text-amber-500" />
                                )}
                                <span className="font-medium">
                                    {t("import_complete")}
                                </span>
                            </div>

                            <div className="grid grid-cols-2 gap-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">{t("trades_created")}:</span>
                                    <span className="font-mono">{result.trades_created}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">{t("cash_transactions")}:</span>
                                    <span className="font-mono">{result.cash_transactions_created}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">{t("duplicates_skipped")}:</span>
                                    <span className="font-mono">{result.duplicates_skipped}</span>
                                </div>
                            </div>

                            {/* Warnings */}
                            {result.warnings.length > 0 && (
                                <div className="mt-2">
                                    <div className="flex items-center gap-1 text-sm text-amber-600 dark:text-amber-400 mb-1">
                                        <FileWarning className="h-4 w-4" />
                                        <span>{t("warnings")} ({result.warnings.length})</span>
                                    </div>
                                    <div className="max-h-24 overflow-y-auto text-xs bg-muted/50 rounded p-2 space-y-1">
                                        {result.warnings.slice(0, 10).map((warning, i) => (
                                            <div key={i} className="text-muted-foreground">
                                                {warning}
                                            </div>
                                        ))}
                                        {result.warnings.length > 10 && (
                                            <div className="text-muted-foreground italic">
                                                ...{t("and_more", { count: result.warnings.length - 10 })}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Errors */}
                            {result.errors.length > 0 && (
                                <div className="mt-2">
                                    <div className="flex items-center gap-1 text-sm text-red-600 dark:text-red-400 mb-1">
                                        <AlertCircle className="h-4 w-4" />
                                        <span>{t("errors")} ({result.errors.length})</span>
                                    </div>
                                    <div className="max-h-24 overflow-y-auto text-xs bg-red-50 dark:bg-red-900/20 rounded p-2 space-y-1">
                                        {result.errors.slice(0, 5).map((error, i) => (
                                            <div key={i} className="text-red-700 dark:text-red-300">
                                                {error.error}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={handleClose}>
                        {result ? t("close") : t("cancel")}
                    </Button>
                    {!result && (
                        <Button
                            onClick={handleUpload}
                            disabled={!selectedFile || uploadMutation.isPending}
                        >
                            {uploadMutation.isPending ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    {t("importing")}
                                </>
                            ) : (
                                t("import")
                            )}
                        </Button>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
