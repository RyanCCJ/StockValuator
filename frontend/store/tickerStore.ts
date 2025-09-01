import { create } from 'zustand';

// --- Type Definitions for API Response ---

// For regular stocks (EQUITY)
interface ScoreBreakdown { [key: string]: number; }
interface AnalysisScore { total_score: number; breakdown: ScoreBreakdown; }
interface FairValueItem { value: number | null; reason: string; }
interface FairValue { growth_value: FairValueItem; dividend_value: FairValueItem; asset_value: FairValueItem; }

interface StockData {
  ticker: string;
  key_metrics: any;
  financial_statements: any[];
  analysis_scores: {
    confidence: AnalysisScore;
    dividend: AnalysisScore;
    value: AnalysisScore;
  };
  fair_value: FairValue;
}

// For ETFs
interface EtfHolding {
  symbol: string;
  name: string;
  weight: string;
}

interface EtfData {
  details: any; // Contains summary and all key metrics from yfinance
  top_holdings: EtfHolding[];
}

// Discriminated union for the analysis data
export type AnalysisData = 
  | { quoteType: 'EQUITY'; data: StockData }
  | { quoteType: 'ETF'; data: EtfData };


export interface Holding {
  shares: number;
  averagePrice: number;
}

// --- Zustand Store Definition ---

interface TickerState {
  selectedTicker: string;
  watchlist: string[];
  analysisData: AnalysisData | null;
  isLoading: boolean;
  error: string | null;
  activePage: string;
  holdings: { [ticker: string]: Holding };
  totalAssets: number;
  setSelectedTicker: (ticker: string) => void;
  fetchAnalysis: (ticker: string) => Promise<void>;
  addTickerToWatchlist: (ticker: string) => void;
  removeTickerFromWatchlist: (ticker: string) => void;
  setActivePage: (page: string) => void;
  setHolding: (ticker: string, shares: number, averagePrice: number) => void;
  removeHolding: (ticker: string) => void;
  setTotalAssets: (assets: number) => void;
}

export const useTickerStore = create<TickerState>((set, get) => ({
  // --- State ---
  selectedTicker: 'AAPL', 
  watchlist: ['AAPL', 'MSFT', 'GOOGL', 'VOO'], // Added an ETF
  analysisData: null,
  isLoading: false,
  error: null,
  activePage: 'dashboard', // Default page
  holdings: {
    'AAPL': { shares: 10, averagePrice: 150 },
    'MSFT': { shares: 5, averagePrice: 300 },
    'VOO': { shares: 10, averagePrice: 450 },
  },
  totalAssets: 100000,

  // --- Actions ---
  setActivePage: (page) => set({ activePage: page }),

  setSelectedTicker: (ticker) => {
    set({ selectedTicker: ticker, analysisData: null, error: null }); // Reset data on new selection
    get().fetchAnalysis(ticker);
  },

  fetchAnalysis: async (ticker) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`http://localhost:8000/api/v1/stock/${ticker}/analysis`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch analysis data');
      }
      const data: AnalysisData = await response.json();
      set({ analysisData: data, isLoading: false });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      set({ error: errorMessage, isLoading: false });
    }
  },

  addTickerToWatchlist: (ticker) => {
    const { watchlist } = get();
    if (!watchlist.includes(ticker)) {
      set({ watchlist: [...watchlist, ticker] });
    }
  },

  removeTickerFromWatchlist: (ticker) => {
    set({ watchlist: get().watchlist.filter((t) => t !== ticker) });
  },

  setHolding: (ticker, shares, averagePrice) => {
    const { holdings } = get();
    const newHoldings = {
      ...holdings,
      [ticker]: { shares, averagePrice },
    };
    set({ holdings: newHoldings });
  },

  removeHolding: (ticker) => {
    const { holdings } = get();
    const newHoldings = { ...holdings };
    delete newHoldings[ticker];
    set({ holdings: newHoldings });
  },

  setTotalAssets: (assets) => set({ totalAssets: assets }),
}));