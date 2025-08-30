'use client';

import React from 'react';
import { useTickerStore } from '@/store/tickerStore';
import { cn } from '@/lib/utils';

const Header = () => {
  const { activePage, setActivePage } = useTickerStore();

  const navItems = ['Dashboard', 'Analysis', 'Portfolio'];

  return (
    <header className="h-16 border-b flex items-center px-6 shrink-0">
      <h1 className="text-lg font-semibold">StockValuator</h1>
      <nav className="ml-auto flex items-center space-x-4">
        {navItems.map((item) => (
          <button
            key={item}
            onClick={() => setActivePage(item.toLowerCase())}
            className={cn(
              'text-sm font-medium transition-colors hover:text-primary',
              activePage === item.toLowerCase()
                ? 'text-primary'
                : 'text-muted-foreground'
            )}
          >
            {item}
          </button>
        ))}
      </nav>
    </header>
  );
};

export default Header;
