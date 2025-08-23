import { create } from 'zustand';

interface TickerState {
  selectedTicker: string;
  setSelectedTicker: (ticker: string) => void;
}

export const useTickerStore = create<TickerState>((set) => ({
  selectedTicker: 'AAPL', // Set a default ticker
  setSelectedTicker: (ticker) => set({ selectedTicker: ticker }),
}));
