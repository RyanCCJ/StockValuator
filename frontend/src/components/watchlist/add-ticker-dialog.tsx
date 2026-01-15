"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
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
import { addWatchlistItem, Category } from "@/services/api";
import { useTranslations } from "next-intl";

interface AddTickerDialogProps {
    accessToken: string | undefined;
    categories?: Category[];
    onAdd: () => void;
}

export function AddTickerDialog({ accessToken, categories = [], onAdd }: AddTickerDialogProps) {
    const t = useTranslations("Watchlist");
    const [isOpen, setIsOpen] = useState(false);
    const [symbol, setSymbol] = useState("");
    const [categoryId, setCategoryId] = useState<string>("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!accessToken || !symbol.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            await addWatchlistItem(
                accessToken,
                symbol.trim().toUpperCase(),
                categoryId || undefined
            );
            setSymbol("");
            setCategoryId("");
            setIsOpen(false);
            onAdd();
        } catch (err) {
            setError(err instanceof Error ? err.message : t('add_error'));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button variant="ghost" size="sm" className="h-6 px-2 text-xs">
                    {t('add_button')}
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[400px]">
                <DialogHeader>
                    <DialogTitle>{t('add_dialog_title')}</DialogTitle>
                    <DialogDescription>
                        {t('add_dialog_desc')}
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="symbol">{t('ticker_symbol')}</Label>
                        <Input
                            id="symbol"
                            placeholder={t('ticker_placeholder')}
                            value={symbol}
                            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                            disabled={isLoading}
                        />
                    </div>
                    {categories.length > 0 && (
                        <div className="space-y-2">
                            <Label htmlFor="category">{t('category_optional')}</Label>
                            <select
                                id="category"
                                className="w-full h-10 px-3 border rounded-md bg-background"
                                value={categoryId}
                                onChange={(e) => setCategoryId(e.target.value)}
                                disabled={isLoading}
                            >
                                <option value="">{t('no_category')}</option>
                                {categories.map((cat) => (
                                    <option key={cat.id} value={cat.id}>
                                        {cat.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                    {error && <p className="text-sm text-destructive">{error}</p>}
                    <div className="flex gap-2 justify-end">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => setIsOpen(false)}
                            disabled={isLoading}
                        >
                            {t('cancel')}
                        </Button>
                        <Button type="submit" disabled={isLoading || !symbol.trim()}>
                            {isLoading ? t('adding') : t('add')}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
