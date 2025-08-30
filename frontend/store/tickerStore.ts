import { create } from 'zustand';

// --- Type Definitions for API Response ---

interface ScoreBreakdown {
  [key: string]: number;
}

interface AnalysisScore {
  total_score: number;
  breakdown: ScoreBreakdown;
}

interface FairValueItem {
  value: number | null;
  reason: string;
}

interface FairValue {
  growth_value: FairValueItem;
  dividend_value: FairValueItem;
  asset_value: FairValueItem;
}

export interface AnalysisData {
  ticker: string;
  finviz_data: any; // Replace 'any' with a more specific type if needed
  roic_data_summary: any[]; // Replace 'any' with a more specific type if needed
  analysis_scores: {
    confidence: AnalysisScore;
    dividend: AnalysisScore;
    value: AnalysisScore;
  };
  fair_value: FairValue;
}

// --- Zustand Store Definition ---

interface TickerState {
  selectedTicker: string;
  watchlist: string[];
  analysisData: AnalysisData | null;
  isLoading: boolean;
  error: string | null;
  activePage: string;
  setSelectedTicker: (ticker: string) => void;
  fetchAnalysis: (ticker: string) => Promise<void>;
  addTickerToWatchlist: (ticker: string) => void;
  removeTickerFromWatchlist: (ticker: string) => void;
  setActivePage: (page: string) => void;
}

export const useTickerStore = create<TickerState>((set, get) => ({
  // --- State ---
  selectedTicker: 'AAPL', 
  watchlist: ['AAPL', 'MSFT', 'GOOGL'], // Default watchlist
  analysisData: null,
  isLoading: false,
  error: null,
  activePage: 'dashboard', // Default page

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
}));
