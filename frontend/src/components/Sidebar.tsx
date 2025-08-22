import React from 'react';

const Sidebar = () => {
  return (
    <aside className="w-64 border-r p-4 shrink-0">
      <h2 className="text-lg font-semibold mb-4">Watchlist</h2>
      {/* Placeholder for watchlist items */}
      <div className="space-y-2">
        <div className="p-2 rounded-md bg-muted text-sm font-medium">AAPL</div>
        <div className="p-2 rounded-md hover:bg-muted/50 text-sm text-muted-foreground">GOOGL</div>
        <div className="p-2 rounded-md hover:bg-muted/50 text-sm text-muted-foreground">MSFT</div>
      </div>
    </aside>
  );
};

export default Sidebar;
