/**
 * API service for backend communication
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

interface TradeData {
    symbol: string;
    date: string;
    type: "buy" | "sell";
    price: number;
    quantity: number;
    fees?: number;
    currency?: string;
    notes?: string;
}

interface Trade extends TradeData {
    id: string;
    user_id: string;
    created_at: string;
    notes?: string;
}

interface TradeListResponse {
    trades: Trade[];
    total: number;
}

async function fetchWithAuth(
    endpoint: string,
    accessToken: string,
    options: RequestInit = {}
): Promise<Response> {
    return fetch(`${BACKEND_URL}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
            ...options.headers,
        },
    });
}

export async function getTrades(accessToken: string): Promise<TradeListResponse> {
    const response = await fetchWithAuth("/trades", accessToken);
    if (!response.ok) {
        throw new Error("Failed to fetch trades");
    }
    return response.json();
}

export async function createTrade(accessToken: string, trade: TradeData): Promise<Trade> {
    const response = await fetchWithAuth("/trades", accessToken, {
        method: "POST",
        body: JSON.stringify(trade),
    });
    if (!response.ok) {
        throw new Error("Failed to create trade");
    }
    return response.json();
}

export async function updateTrade(
    accessToken: string,
    tradeId: string,
    trade: Partial<TradeData>
): Promise<Trade> {
    const response = await fetchWithAuth(`/trades/${tradeId}`, accessToken, {
        method: "PUT",
        body: JSON.stringify(trade),
    });
    if (!response.ok) {
        throw new Error("Failed to update trade");
    }
    return response.json();
}

export async function deleteTrade(accessToken: string, tradeId: string): Promise<void> {
    const response = await fetchWithAuth(`/trades/${tradeId}`, accessToken, {
        method: "DELETE",
    });
    if (!response.ok) {
        throw new Error("Failed to delete trade");
    }
}

// Portfolio API
interface Holding {
    symbol: string;
    quantity: number;
    avg_cost: number;
    current_price: number | null;
    current_value: number;
    cost_basis: number;
    unrealized_pnl: number;
    unrealized_pnl_percent: number;
    price_change: number | null;
    price_change_percent: number | null;
}

interface PortfolioSummary {
    total_value: number;
    total_cost: number;
    total_pnl: number;
    total_pnl_percent: number;
    realized_pnl: number;
    unrealized_pnl: number;
    holdings: Holding[];
    holdings_count: number;
    cash_balance: number;
    total_portfolio: number;
    cash_ratio: number;
}

export async function getPortfolioSummary(accessToken: string): Promise<PortfolioSummary> {
    const response = await fetchWithAuth("/portfolio/summary", accessToken);
    if (!response.ok) {
        throw new Error("Failed to fetch portfolio summary");
    }
    return response.json();
}

// Market Data API
interface StockPrice {
    symbol: string;
    price: number;
    currency: string;
    previous_close: number | null;
    change: number | null;
    change_percent: number | null;
}

export async function getStockPrice(symbol: string): Promise<StockPrice> {
    const response = await fetch(`${BACKEND_URL}/market/price/${symbol}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch price for ${symbol}`);
    }
    return response.json();
}

// Watchlist API
interface WatchlistItem {
    id: string;
    symbol: string;
    user_id: string;
    category_id: string | null;
    created_at: string;
}

interface Category {
    id: string;
    name: string;
    user_id: string;
    created_at: string;
    items: WatchlistItem[];
}

interface WatchlistResponse {
    categories: Category[];
    uncategorized: WatchlistItem[];
}

export async function getWatchlist(accessToken: string): Promise<WatchlistResponse> {
    const response = await fetchWithAuth("/watchlist", accessToken);
    if (!response.ok) {
        throw new Error("Failed to fetch watchlist");
    }
    return response.json();
}

export async function addWatchlistItem(
    accessToken: string,
    symbol: string,
    categoryId?: string
): Promise<WatchlistItem> {
    const response = await fetchWithAuth("/watchlist/items", accessToken, {
        method: "POST",
        body: JSON.stringify({ symbol, category_id: categoryId }),
    });
    if (!response.ok) {
        throw new Error("Failed to add to watchlist");
    }
    return response.json();
}

export async function removeWatchlistItem(accessToken: string, itemId: string): Promise<void> {
    const response = await fetchWithAuth(`/watchlist/items/${itemId}`, accessToken, {
        method: "DELETE",
    });
    if (!response.ok) {
        throw new Error("Failed to remove from watchlist");
    }
}

export async function createCategory(accessToken: string, name: string): Promise<Category> {
    const response = await fetchWithAuth("/watchlist/categories", accessToken, {
        method: "POST",
        body: JSON.stringify({ name }),
    });
    if (!response.ok) {
        throw new Error("Failed to create category");
    }
    return response.json();
}

export async function deleteCategory(accessToken: string, categoryId: string): Promise<void> {
    const response = await fetchWithAuth(`/watchlist/categories/${categoryId}`, accessToken, {
        method: "DELETE",
    });
    if (!response.ok) {
        throw new Error("Failed to delete category");
    }
}

// Cash Transaction API
interface CashTransaction {
    id: string;
    user_id: string;
    date: string;
    type: "deposit" | "withdraw";
    amount: number;
    currency: string;
    notes?: string;
    created_at: string;
}

interface CashTransactionData {
    date: string;
    type: "deposit" | "withdraw";
    amount: number;
    currency?: string;
    notes?: string;
}

interface CashTransactionListResponse {
    transactions: CashTransaction[];
    total: number;
    balance: number;
}

export async function getCashTransactions(accessToken: string): Promise<CashTransactionListResponse> {
    const response = await fetchWithAuth("/cash", accessToken);
    if (!response.ok) {
        throw new Error("Failed to fetch cash transactions");
    }
    return response.json();
}

export async function createCashTransaction(
    accessToken: string,
    data: CashTransactionData
): Promise<CashTransaction> {
    const response = await fetchWithAuth("/cash", accessToken, {
        method: "POST",
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error("Failed to create cash transaction");
    }
    return response.json();
}

export async function updateCashTransaction(
    accessToken: string,
    transactionId: string,
    data: Partial<CashTransactionData>
): Promise<CashTransaction> {
    const response = await fetchWithAuth(`/cash/${transactionId}`, accessToken, {
        method: "PATCH",
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error("Failed to update cash transaction");
    }
    return response.json();
}

export async function deleteCashTransaction(accessToken: string, transactionId: string): Promise<void> {
    const response = await fetchWithAuth(`/cash/${transactionId}`, accessToken, {
        method: "DELETE",
    });
    if (!response.ok) {
        throw new Error("Failed to delete cash transaction");
    }
}

// Export functions
export async function exportTrades(accessToken: string, format: "csv" | "xlsx"): Promise<Blob> {
    const response = await fetchWithAuth(`/export/trades?format=${format}`, accessToken);
    if (!response.ok) {
        throw new Error("Failed to export trades");
    }
    return response.blob();
}

export async function exportCash(accessToken: string, format: "csv" | "xlsx"): Promise<Blob> {
    const response = await fetchWithAuth(`/export/cash?format=${format}`, accessToken);
    if (!response.ok) {
        throw new Error("Failed to export cash transactions");
    }
    return response.blob();
}

// Import functions
export interface ImportResult {
    success_count: number;
    error_count: number;
    errors: Array<{ row: number; error: string }>;
}

export async function importTrades(accessToken: string, file: File): Promise<ImportResult> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${BACKEND_URL}/import/trades`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${accessToken}`,
        },
        body: formData,
    });
    if (!response.ok) {
        throw new Error("Failed to import trades");
    }
    return response.json();
}

export async function importCash(accessToken: string, file: File): Promise<ImportResult> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${BACKEND_URL}/import/cash`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${accessToken}`,
        },
        body: formData,
    });
    if (!response.ok) {
        throw new Error("Failed to import cash transactions");
    }
    return response.json();
}

export type {
    Trade, TradeData, TradeListResponse,
    PortfolioSummary, Holding, StockPrice,
    WatchlistItem, Category, WatchlistResponse,
    CashTransaction, CashTransactionData, CashTransactionListResponse
};
