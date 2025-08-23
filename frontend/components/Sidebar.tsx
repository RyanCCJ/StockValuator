'use client';

import React, { useState } from 'react';
import { useTickerStore } from '@/store/tickerStore';
import { cn } from '@/lib/utils';

const Sidebar = () => {
  // Local state for the input field
  const [newTicker, setNewTicker] = useState('');
  
  // Global state from Zustand
  const { selectedTicker, setSelectedTicker } = useTickerStore();
  
  // Placeholder for the watchlist - we will make this dynamic later
  const [watchlist, setWatchlist] = useState(['AAPL', 'GOOGL', 'MSFT']);

  const handleAddTicker = () => {
    if (newTicker && !watchlist.includes(newTicker.toUpperCase())) {
      const upperCaseTicker = newTicker.toUpperCase();
      setWatchlist([...watchlist, upperCaseTicker]);
      setSelectedTicker(upperCaseTicker);
      setNewTicker('');
    }
  };

  return (
    <aside className="w-64 border-r p-4 shrink-0 bg-muted/40 flex flex-col">
      <h2 className="text-lg font-semibold mb-4">Watchlist</h2>
      
      <div className="flex w-full max-w-sm items-center space-x-2 mb-4">
        <input 
          type="text" 
          placeholder="Add Ticker..." 
          value={newTicker}
          onChange={(e) => setNewTicker(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAddTicker()}
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <button 
          onClick={handleAddTicker}
          className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
        >
          Add
        </button>
      </div>

      <div className="space-y-2 overflow-y-auto">
        {watchlist.map((ticker) => (
          <div
            key={ticker}
            onClick={() => setSelectedTicker(ticker)}
            className={cn(
              "p-2 rounded-md text-sm font-medium cursor-pointer",
              selectedTicker === ticker 
                ? "bg-primary text-primary-foreground" 
                : "hover:bg-accent hover:text-accent-foreground text-muted-foreground"
            )}
          >
            {ticker}
          </div>
        ))}
      </div>
    </aside>
  );
};

export default Sidebar;