import React from 'react';

const Header = () => {
    return (
        <header className="h-16 border-b flex items-center px-6 shrink-0">
            <h1 className="text-lg font-semibold">StockValuator</h1>
            <nav className="ml-auto flex items-center space-x-4">
                <a href="#" className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary">Dashboard</a>
                <a href="#" className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary">Analysis</a>
                <a href="#" className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary">Portfolio</a>
            </nav>
        </header>
    );
};

export default Header;