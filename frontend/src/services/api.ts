/**
 * API service for backend communication
 * All requests go through the Next.js API proxy at /api/*
 */

// API base URL - uses Next.js API routes which proxy to the backend
const API_BASE = "/api";

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
    return fetch(`${API_BASE}${endpoint}`, {
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
    const response = await fetch(`${API_BASE}/market/price/${symbol}`);
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

    const response = await fetch(`${API_BASE}/import/trades`, {
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

    const response = await fetch(`${API_BASE}/import/cash`, {
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

// Technical Analysis API
interface OHLCVData {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

interface SMAIndicator {
    ma5: (number | null)[];
    ma20: (number | null)[];
    ma60: (number | null)[];
}

interface MACDIndicator {
    line: (number | null)[];
    signal: (number | null)[];
    histogram: (number | null)[];
}

interface BollingerBandsIndicator {
    upper: (number | null)[];
    middle: (number | null)[];
    lower: (number | null)[];
}

interface StochasticIndicator {
    k: (number | null)[];
    d: (number | null)[];
    j: (number | null)[];
}

interface TechnicalIndicators {
    sma: SMAIndicator;
    rsi: (number | null)[];
    macd: MACDIndicator;
    bollinger: BollingerBandsIndicator;
    stochastic: StochasticIndicator;
    volume: number[];
}

interface TechnicalDataResponse {
    symbol: string;
    ohlcv: OHLCVData[];
    indicators: TechnicalIndicators;
}

export async function getTechnicalData(
    symbol: string,
    period: "1mo" | "3mo" | "6mo" | "1y" | "2y" = "1y"
): Promise<TechnicalDataResponse> {
    const response = await fetch(`${API_BASE}/market/technical/${symbol}?period=${period}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch technical data for ${symbol}`);
    }
    return response.json();
}

// Fundamental Data API
interface InstitutionalHolder {
    holder: string;
    percent: number | null;
}

interface TopHolding {
    symbol: string;
    name: string;
    percent: number;
}

interface SectorWeighting {
    sector: string;
    weight: number;
}

interface FundamentalDataResponse {
    symbol: string;
    is_etf: boolean;
    long_name: string | null;
    market_cap: number | null;
    beta: number | null;
    fifty_two_week_high: number | null;
    fifty_two_week_low: number | null;
    trailing_pe: number | null;
    dividend_yield: number | null;
    last_updated: string;

    // Stock/Crypto specific
    description?: string | null;
    coin_image_url?: string | null;
    sector?: string | null;
    industry?: string | null;
    forward_pe?: number | null;
    trailing_eps?: number | null;
    forward_eps?: number | null;
    payout_ratio?: number | null;
    profit_margins?: number | null;
    revenue_growth?: number | null;
    analyst_rating?: string | null;
    book_value?: number | null;
    institutional_holders?: InstitutionalHolder[];

    // ETF specific
    beta_3_year?: number | null;
    expense_ratio?: number | null;
    top_holdings?: TopHolding[];
    sector_weightings?: SectorWeighting[];
}

export async function getFundamentalData(symbol: string): Promise<FundamentalDataResponse> {
    const response = await fetch(`${API_BASE}/market/fundamental/${symbol}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch fundamental data for ${symbol}`);
    }
    return response.json();
}

// Alerts API
interface PriceAlert {
    id: string;
    symbol: string;
    target_price: number;
    initial_price: number;
    status: "active" | "triggered" | "inactive";
    created_at: string;
    triggered_at: string | null;
}

interface AlertListResponse {
    alerts: PriceAlert[];
    count: number;
}

interface CreateAlertData {
    symbol: string;
    target_price: number;
}

export async function getAlerts(accessToken: string): Promise<AlertListResponse> {
    const response = await fetchWithAuth("/alerts", accessToken);
    if (!response.ok) {
        throw new Error("Failed to fetch alerts");
    }
    return response.json();
}

export async function createAlert(accessToken: string, data: CreateAlertData): Promise<PriceAlert> {
    const response = await fetchWithAuth("/alerts", accessToken, {
        method: "POST",
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error("Failed to create alert");
    }
    return response.json();
}

export async function deleteAlert(accessToken: string, alertId: string): Promise<void> {
    const response = await fetchWithAuth(`/alerts/${alertId}`, accessToken, {
        method: "DELETE",
    });
    if (!response.ok) {
        throw new Error("Failed to delete alert");
    }
}

export type {
    Trade, TradeData, TradeListResponse,
    PortfolioSummary, Holding, StockPrice,
    WatchlistItem, Category, WatchlistResponse,
    CashTransaction, CashTransactionData, CashTransactionListResponse,
    TechnicalDataResponse, OHLCVData, TechnicalIndicators,
    FundamentalDataResponse, InstitutionalHolder, TopHolding, SectorWeighting,
    PriceAlert, AlertListResponse, CreateAlertData,
    ValueAnalysisResponse, ScoreBreakdown, ConfidenceScore, DividendScore,
    ValueScoreType, FairValueEstimate, AIScoreResponse
};

interface ScoreBreakdown {
    name: string;
    score: number;
    max_score: number;
    reason: string;
}

interface ConfidenceScore {
    total: number;
    max_possible: number;
    breakdown: ScoreBreakdown[];
    moat_score: number | null;
    risk_score: number | null;
}

interface DividendScore {
    total: number;
    max_possible: number;
    breakdown: ScoreBreakdown[];
}

interface ValueScoreType {
    total: number;
    max_possible: number;
    breakdown: ScoreBreakdown[];
}

interface FairValueEstimate {
    model: "growth" | "dividend" | "asset";
    fair_value: number | null;
    current_price: number | null;
    is_undervalued: boolean;
    explanation: string;
}

interface ValueAnalysisResponse {
    symbol: string;
    data_status: "complete" | "partial" | "insufficient";
    data_source: string | null;
    confidence: ConfidenceScore;
    dividend: DividendScore;
    value: ValueScoreType;
    fair_value?: FairValueEstimate;
}

interface AIScoreResponse {
    symbol: string;
    score_type: string;
    score: number | null;
    breakdown: Record<string, unknown> | null;
    reasoning: string | null;
    prompt: string | null;
    error: string | null;
    manual_entry_required: boolean;
}

// Custom error class to preserve HTTP status
export class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
        super(message);
        this.status = status;
        this.name = "ApiError";
    }
}

export async function getValueAnalysis(symbol: string): Promise<ValueAnalysisResponse> {
    const response = await fetch(`${API_BASE}/analysis/${symbol}/value`);
    if (!response.ok) {
        throw new ApiError(`Failed to fetch value analysis for ${symbol}`, response.status);
    }
    return response.json();
}

export async function getFairValue(
    symbol: string,
    model: "growth" | "dividend" | "asset" = "growth",
    expectedReturn: number = 0.04,
    pbThreshold: number = 0.8
): Promise<FairValueEstimate> {
    const response = await fetch(`${API_BASE}/analysis/${symbol}/fair-value`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            model,
            expected_return: expectedReturn,
            pb_threshold: pbThreshold,
        }),
    });
    if (!response.ok) {
        throw new Error(`Failed to fetch fair value for ${symbol}`);
    }
    return response.json();
}

export async function getAIScore(
    symbol: string,
    scoreType: "moat" | "risk",
    forceRefresh: boolean = false
): Promise<AIScoreResponse> {
    const response = await fetch(`${API_BASE}/analysis/${symbol}/ai-score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            score_type: scoreType,
            force_refresh: forceRefresh,
        }),
    });
    if (!response.ok) {
        throw new Error(`Failed to fetch AI score for ${symbol}`);
    }
    return response.json();
}

export async function getAIPrompt(
    symbol: string,
    scoreType: "moat" | "risk"
): Promise<{ symbol: string; score_type: string; prompt: string }> {
    const response = await fetch(`${API_BASE}/analysis/${symbol}/ai-prompt/${scoreType}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch AI prompt for ${symbol}`);
    }
    return response.json();
}
