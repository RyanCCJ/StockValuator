"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Trash2, Loader2 } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createAlert, getAlerts, deleteAlert } from "@/services/api";

interface SetAlertDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    symbol: string;
    currentPrice?: number;
}

export function SetAlertDialog({
    open,
    onOpenChange,
    symbol,
    currentPrice,
}: SetAlertDialogProps) {
    const { data: session } = useSession();
    const t = useTranslations("Alerts");
    const queryClient = useQueryClient();
    const [targetPrice, setTargetPrice] = useState<string>("");

    const accessToken = (session as { accessToken?: string })?.accessToken;

    // Fetch existing alerts
    const { data: alertsData, isLoading: alertsLoading } = useQuery({
        queryKey: ["alerts"],
        queryFn: () => getAlerts(accessToken!),
        enabled: !!accessToken && open,
    });

    // Filter alerts for current symbol
    const symbolAlerts = alertsData?.alerts.filter(
        (alert) => alert.symbol.toUpperCase() === symbol.toUpperCase()
    ) || [];

    const createMutation = useMutation({
        mutationFn: async () => {
            if (!accessToken || !targetPrice) return;
            return createAlert(accessToken, {
                symbol,
                target_price: parseFloat(targetPrice),
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["alerts"] });
            setTargetPrice("");
        },
    });

    const deleteMutation = useMutation({
        mutationFn: async (alertId: string) => {
            if (!accessToken) return;
            return deleteAlert(accessToken, alertId);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["alerts"] });
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        createMutation.mutate();
    };

    const priceDirection = currentPrice && targetPrice
        ? parseFloat(targetPrice) > currentPrice
            ? t("above_current")
            : t("below_current")
        : "";

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>{t("set_alert_for", { symbol })}</DialogTitle>
                    <DialogDescription>
                        {currentPrice && (
                            <span>
                                {t("current_price")}: <strong>${currentPrice.toFixed(2)}</strong>
                            </span>
                        )}
                    </DialogDescription>
                </DialogHeader>

                {/* Existing alerts section */}
                {symbolAlerts.length > 0 && (
                    <div className="border rounded-lg p-3 bg-muted/30">
                        <div className="text-sm font-medium mb-2">{t("existing_alerts")}</div>
                        <div className="space-y-2">
                            {symbolAlerts.map((alert) => (
                                <div
                                    key={alert.id}
                                    className="flex items-center justify-between text-sm bg-background rounded px-3 py-2"
                                >
                                    <div className="flex items-center gap-2">
                                        <span className="font-mono">${alert.target_price.toFixed(2)}</span>
                                        <span className={`text-xs px-1.5 py-0.5 rounded ${alert.status === "active"
                                                ? "bg-green-500/20 text-green-500"
                                                : alert.status === "triggered"
                                                    ? "bg-amber-500/20 text-amber-500"
                                                    : "bg-gray-500/20 text-gray-500"
                                            }`}>
                                            {alert.status}
                                        </span>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                                        onClick={() => deleteMutation.mutate(alert.id)}
                                        disabled={deleteMutation.isPending}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {alertsLoading && (
                    <div className="flex items-center justify-center py-4">
                        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="target-price" className="text-right">
                                {t("target_price")}
                            </Label>
                            <div className="col-span-3">
                                <Input
                                    id="target-price"
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    placeholder="0.00"
                                    value={targetPrice}
                                    onChange={(e) => setTargetPrice(e.target.value)}
                                    required
                                />
                                {priceDirection && (
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {priceDirection}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                            {t("cancel")}
                        </Button>
                        <Button type="submit" disabled={createMutation.isPending || !targetPrice}>
                            {createMutation.isPending ? t("creating") : t("create_alert")}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
