"use client";

import { useState, useEffect, useCallback } from "react";
import { Link, usePathname } from "@/i18n/routing";
import { useTranslations } from "next-intl";
import { signOut } from "next-auth/react";
import { TrendingUp, LogOut, Menu } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { LanguageToggle } from "@/components/layout/language-toggle";
import { CurrencyToggle } from "@/components/layout/currency-toggle";
import { AddTickerDialog } from "@/components/watchlist/add-ticker-dialog";
import { CategoryManager } from "@/components/watchlist/category-manager";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
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
    const [isMobileOpen, setIsMobileOpen] = useState(false);
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

    const renderSidebarContent = (onNavigate?: () => void) => (
        <div className="flex h-full flex-col bg-card">
            <div className="p-6 flex items-center gap-2">
                <TrendingUp className="h-6 w-6 text-foreground" />
                <h2 className="text-lg font-semibold">StockValuator</h2>
            </div>

            {/* Navigation */}
            <nav className="px-4 space-y-1">
                <Link
                    href="/dashboard"
                    onClick={onNavigate}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md ${pathname === "/dashboard"
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-accent"
                        }`}
                >
                    {t('dashboard')}
                </Link>
                <Link
                    href="/dashboard/trades"
                    onClick={onNavigate}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md ${pathname === "/dashboard/trades"
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-accent"
                        }`}
                >
                    {t('trades')}
                </Link>
                <Link
                    href="/dashboard/assets"
                    onClick={onNavigate}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md ${pathname === "/dashboard/assets"
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-accent"
                        }`}
                >
                    {t('assets')}
                </Link>
                <Link
                    href="/dashboard/market-cycle"
                    onClick={onNavigate}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md ${pathname === "/dashboard/market-cycle"
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-accent"
                        }`}
                >
                    {t('market')}
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
                                {[...watchlist.uncategorized].sort((a, b) => a.symbol.localeCompare(b.symbol)).map((item) => (
                                    <WatchlistItemRow
                                        key={item.id}
                                        item={item}
                                        price={prices[item.symbol]}
                                        pathname={pathname}
                                        formatMoney={formatMoney}
                                        onRemove={handleRemoveItem}
                                        onNavigate={onNavigate}
                                    />
                                ))}
                            </div>
                        )}

                        {/* Categories */}
                        {watchlist.categories.map((category) => (
                            <div key={category.id}>
                                <div className="text-xs font-medium text-muted-foreground mb-1 px-2">
                                    {category.name}
                                </div>
                                {[...category.items].sort((a, b) => a.symbol.localeCompare(b.symbol)).map((item) => (
                                    <WatchlistItemRow
                                        key={item.id}
                                        item={item}
                                        price={prices[item.symbol]}
                                        pathname={pathname}
                                        formatMoney={formatMoney}
                                        onRemove={handleRemoveItem}
                                        onNavigate={onNavigate}
                                    />
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
        </div>
    );

    return (
        <>
            <aside className="hidden md:flex w-64 flex-col border-r bg-card">
                {renderSidebarContent()}
            </aside>

            <div className="md:hidden w-full flex items-center p-4 border-b bg-card gap-4">
                <Sheet open={isMobileOpen} onOpenChange={setIsMobileOpen}>
                    <SheetTrigger asChild>
                        <Button variant="ghost" size="icon">
                            <Menu className="h-6 w-6" />
                        </Button>
                    </SheetTrigger>
                    <SheetContent
                        side="left"
                        className="p-0 w-64"
                        closeIcon={<Menu className="h-6 w-6" />}
                        closeClassName={cn(
                            "top-5 right-6 opacity-100",
                            buttonVariants({ variant: "ghost", size: "icon" })
                        )}
                    >
                        <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
                        {renderSidebarContent(() => setIsMobileOpen(false))}
                    </SheetContent>
                </Sheet>
                <div className="flex items-center gap-2">
                    <TrendingUp className="h-6 w-6 text-foreground" />
                    <h2 className="text-lg font-semibold">StockValuator</h2>
                </div>
            </div>
        </>
    );
}

interface WatchlistItemRowProps {
    item: WatchlistItem;
    price: StockPrice | undefined;
    pathname: string;
    formatMoney: (val: number) => string;
    onRemove: (id: string) => void;
    onNavigate?: () => void;
}

const WatchlistItemRow = ({ item, price, pathname, formatMoney, onRemove, onNavigate }: WatchlistItemRowProps) => {
    const isActive = pathname.includes(`/dashboard/stock/${item.symbol}`);

    return (
        <div className={`flex items-center justify-between py-1.5 px-2 rounded hover:bg-accent/50 group text-sm ${isActive ? 'bg-accent' : ''}`}>
            <Link
                href={`/dashboard/stock/${item.symbol}`}
                className="flex-1 flex items-center gap-2"
                onClick={onNavigate}
            >
                <span className="font-medium">{item.symbol}</span>
                {price && (
                    <div className="flex-1 flex justify-end">
                        <div className="text-right">
                            <div className="text-xs">{formatMoney(price.price)}</div>
                            <div
                                className={`text-xs ${(price.change_percent || 0) >= 0
                                    ? "text-green-600 dark:text-green-400"
                                    : "text-red-600 dark:text-red-400"
                                    }`}
                            >
                                {price.change_percent != null
                                    ? `${price.change_percent >= 0 ? "+" : ""}${price.change_percent.toFixed(2)}%`
                                    : ""}
                            </div>
                        </div>
                    </div>
                )}
            </Link>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    onRemove(item.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive text-xs ml-2"
            >
                ✕
            </button>
        </div>
    );
};
