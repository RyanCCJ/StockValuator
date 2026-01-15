"use client";

import { useState, useEffect, useCallback } from "react";
import { Link, usePathname } from "@/i18n/routing";
import { useTranslations } from "next-intl";
import { signOut } from "next-auth/react";
import { TrendingUp, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { LanguageToggle } from "@/components/layout/language-toggle";
import { CurrencyToggle } from "@/components/layout/currency-toggle";
import { AddTickerDialog } from "@/components/watchlist/add-ticker-dialog";
import { CategoryManager } from "@/components/watchlist/category-manager";
import {
    getWatchlist,
    removeWatchlistItem,
    WatchlistResponse,
    WatchlistItem,
    getStockPrice,
    StockPrice,
} from "@/services/api";
import { useCurrency } from "@/context/currency-context";

interface SidebarProps {
    accessToken: string | undefined;
}

export function Sidebar({ accessToken }: SidebarProps) {
    const t = useTranslations('Sidebar');
    const pathname = usePathname();
    const [watchlist, setWatchlist] = useState<WatchlistResponse | null>(null);
    const [prices, setPrices] = useState<Record<string, StockPrice>>({});
    const [isLoading, setIsLoading] = useState(true);
    const { formatMoney } = useCurrency();

    const fetchWatchlist = useCallback(async () => {
        if (!accessToken) return;
        try {
            const data = await getWatchlist(accessToken);
            setWatchlist(data);

            // Fetch prices for all symbols
            const allSymbols = [
                ...data.uncategorized.map((i) => i.symbol),
                ...data.categories.flatMap((c) => c.items.map((i) => i.symbol)),
            ];

            const uniqueSymbols = [...new Set(allSymbols)];
            const pricePromises = uniqueSymbols.map(async (symbol) => {
                try {
                    const price = await getStockPrice(symbol);
                    return { symbol, price };
                } catch {
                    return { symbol, price: null };
                }
            });

            const results = await Promise.all(pricePromises);
            const priceMap: Record<string, StockPrice> = {};
            results.forEach((r) => {
                if (r.price) priceMap[r.symbol] = r.price;
            });
            setPrices(priceMap);
        } catch (error) {
            console.error("Failed to fetch watchlist:", error);
        } finally {
            setIsLoading(false);
        }
    }, [accessToken]);

    useEffect(() => {
        fetchWatchlist();
    }, [fetchWatchlist]);

    const handleRemoveItem = async (itemId: string) => {
        if (!accessToken) return;
        try {
            await removeWatchlistItem(accessToken, itemId);
            fetchWatchlist();
        } catch (error) {
            console.error("Failed to remove item:", error);
        }
    };

    // formatMoney is now provided by useCurrency()

    const WatchlistItemRow = ({ item }: { item: WatchlistItem }) => {
        const price = prices[item.symbol];
        return (
            <div className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-accent/50 group text-sm">
                <div className="flex items-center gap-2">
                    <span className="font-medium">{item.symbol}</span>
                </div>
                <div className="flex items-center gap-2">
                    {price && (
                        <div className="text-right">
                            <div className="text-xs">{formatMoney(price.price)}</div>
                            <div
                                className={`text-xs ${(price.change_percent || 0) >= 0
                                    ? "text-green-600 dark:text-green-400"
                                    : "text-red-600 dark:text-red-400"
                                    }`}
                            >
                                {price.change_percent !== null
                                    ? `${price.change_percent >= 0 ? "+" : ""}${price.change_percent.toFixed(2)}%`
                                    : ""}
                            </div>
                        </div>
                    )}
                    <button
                        onClick={() => handleRemoveItem(item.id)}
                        className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive text-xs"
                    >
                        ✕
                    </button>
                </div>
            </div>
        );
    };

    return (
        <aside className="hidden md:flex w-64 flex-col border-r bg-card">
            <div className="p-6 flex items-center gap-2">
                <TrendingUp className="h-6 w-6 text-foreground" />
                <h2 className="text-lg font-semibold">StockValuator</h2>
            </div>

            {/* Navigation */}
            <nav className="px-4 space-y-1">
                <Link
                    href="/dashboard"
                    className={`flex items-center gap-2 px-3 py-2 rounded-md ${pathname === "/dashboard"
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-accent"
                        }`}
                >
                    {t('dashboard')}
                </Link>
                <Link
                    href="/dashboard/trades"
                    className={`flex items-center gap-2 px-3 py-2 rounded-md ${pathname === "/dashboard/trades"
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-accent"
                        }`}
                >
                    {t('trades')}
                </Link>
                <Link
                    href="/dashboard/assets"
                    className={`flex items-center gap-2 px-3 py-2 rounded-md ${pathname === "/dashboard/assets"
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-accent"
                        }`}
                >
                    {t('assets')}
                </Link>
            </nav>

            {/* Watchlist */}
            <div className="flex-1 px-4 mt-6 overflow-y-auto">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-muted-foreground">{t('watchlist')}</h3>
                    <div className="flex items-center gap-1">
                        <AddTickerDialog
                            accessToken={accessToken}
                            categories={watchlist?.categories || []}
                            onAdd={fetchWatchlist}
                        />
                        <CategoryManager
                            accessToken={accessToken}
                            categories={watchlist?.categories || []}
                            onUpdate={fetchWatchlist}
                        />
                    </div>
                </div>

                {isLoading ? (
                    <div className="text-xs text-muted-foreground py-2">{t('loading')}</div>
                ) : watchlist ? (
                    <div className="space-y-3">
                        {/* Uncategorized items */}
                        {watchlist.uncategorized.length > 0 && (
                            <div>
                                {watchlist.uncategorized.map((item) => (
                                    <WatchlistItemRow key={item.id} item={item} />
                                ))}
                            </div>
                        )}

                        {/* Categories */}
                        {watchlist.categories.map((category) => (
                            <div key={category.id}>
                                <div className="text-xs font-medium text-muted-foreground mb-1 px-2">
                                    {category.name}
                                </div>
                                {category.items.map((item) => (
                                    <WatchlistItemRow key={item.id} item={item} />
                                ))}
                            </div>
                        ))}

                        {watchlist.uncategorized.length === 0 &&
                            watchlist.categories.length === 0 && (
                                <div className="text-xs text-muted-foreground py-2 text-center">
                                    {t('no_stocks')}
                                </div>
                            )}
                    </div>
                ) : null}
            </div>

            {/* Bottom actions */}
            <div className="p-4 border-t space-y-2">
                <ThemeToggle />
                <LanguageToggle />
                <CurrencyToggle />
                <Button
                    variant="ghost"
                    className="w-full justify-start text-muted-foreground"
                    onClick={() => signOut({ callbackUrl: "/login" })}
                >
                    <LogOut className="mr-2 h-4 w-4" />
                    {t('logout')}
                </Button>
            </div>
        </aside>
    );
}
