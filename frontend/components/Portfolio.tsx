'use client';

import React, { useEffect, useState } from 'react';
import { useTickerStore, Holding } from '@/store/tickerStore';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Trash2, Edit, PlusCircle } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const API_BASE_URL = 'http://localhost:8000';

// --- Child Components ---

const HoldingDialog = ({ holding, tickerName }: { holding?: Holding; tickerName?: string }) => {
  const [ticker, setTicker] = useState(tickerName || '');
  const [shares, setShares] = useState(holding?.shares.toString() || '');
  const [price, setPrice] = useState(holding?.averagePrice.toString() || '');
  const { setHolding } = useTickerStore();

  const handleSubmit = () => {
    const sharesNum = parseFloat(shares);
    const priceNum = parseFloat(price);
    if (ticker && !isNaN(sharesNum) && !isNaN(priceNum)) {
      setHolding(ticker.toUpperCase(), sharesNum, priceNum);
    }
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{tickerName ? 'Edit' : 'Add'} Holding</DialogTitle>
      </DialogHeader>
      <div className="grid gap-4 py-4">
        <div className="grid grid-cols-4 items-center gap-4">
          <Label htmlFor="ticker" className="text-right">Ticker</Label>
          <Input id="ticker" value={ticker} onChange={(e) => setTicker(e.target.value)} className="col-span-3" disabled={!!tickerName} />
        </div>
        <div className="grid grid-cols-4 items-center gap-4">
          <Label htmlFor="shares" className="text-right">Shares</Label>
          <Input id="shares" type="number" value={shares} onChange={(e) => setShares(e.target.value)} className="col-span-3" />
        </div>
        <div className="grid grid-cols-4 items-center gap-4">
          <Label htmlFor="price" className="text-right">Average Price</Label>
          <Input id="price" type="number" value={price} onChange={(e) => setPrice(e.target.value)} className="col-span-3" />
        </div>
      </div>
      <DialogFooter>
        <DialogClose asChild>
          <Button type="submit" onClick={handleSubmit}>Save changes</Button>
        </DialogClose>
      </DialogFooter>
    </DialogContent>
  );
};

const PortfolioSummary = ({ value, totalAssets, setTotalAssets }: { value: number; totalAssets: number; setTotalAssets: (val: number) => void; }) => {
  const cash = totalAssets - value;
  const allocation = totalAssets > 0 ? (value / totalAssets) * 100 : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio Summary</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="flex flex-col space-y-1.5">
          <Label>Total Assets</Label>
          <Input 
            type="number" 
            value={totalAssets}
            onChange={(e) => setTotalAssets(parseFloat(e.target.value) || 0)}
            placeholder="Enter total assets"
          />
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Portfolio Value</p>
          <p className="text-2xl font-bold">${value.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Cash</p>
          <p className="text-2xl font-bold">${cash.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Allocation</p>
          <p className="text-2xl font-bold">{allocation.toFixed(2)}%</p>
        </div>
      </CardContent>
    </Card>
  );
};

const HoldingsTable = ({ holdings, tickerPrices, removeHolding }: any) => {
  const totalPortfolioValue = Object.entries(holdings).reduce((acc, [ticker, holding]: [string, any]) => {
    const currentPrice = tickerPrices[ticker] || 0;
    return acc + holding.shares * currentPrice;
  }, 0);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Holdings</CardTitle>
          <CardDescription>Manage your stock portfolio below.</CardDescription>
        </div>
        <Dialog>
          <DialogTrigger asChild>
            <Button size="sm" className="gap-1">
              <PlusCircle className="h-4 w-4" />
              Add New
            </Button>
          </DialogTrigger>
          <HoldingDialog />
        </Dialog>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Ticker</TableHead>
              <TableHead>Shares</TableHead>
              <TableHead>Avg. Price</TableHead>
              <TableHead>Current Price</TableHead>
              <TableHead>P/L</TableHead>
              <TableHead>Total Value</TableHead>
              <TableHead>% of Portfolio</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Object.keys(holdings).length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center">No holdings yet. Add one to get started.</TableCell>
              </TableRow>
            ) : (
              Object.entries(holdings).map(([ticker, holding]: [string, any]) => {
                const currentPrice = tickerPrices[ticker] || 0;
                const totalValue = holding.shares * currentPrice;
                const profitLoss = (currentPrice - holding.averagePrice) * holding.shares;
                const percentageOfPortfolio = totalPortfolioValue > 0 ? (totalValue / totalPortfolioValue) * 100 : 0;
                const isProfit = profitLoss >= 0;

                return (
                  <TableRow key={ticker}>
                    <TableCell className="font-medium">{ticker}</TableCell>
                    <TableCell>{holding.shares}</TableCell>
                    <TableCell>${holding.averagePrice.toFixed(2)}</TableCell>
                    <TableCell>${currentPrice > 0 ? currentPrice.toFixed(2) : 'Loading...'}</TableCell>
                    <TableCell className={isProfit ? 'text-green-500' : 'text-red-500'}>
                      ${profitLoss.toFixed(2)}
                    </TableCell>
                    <TableCell>${totalValue.toFixed(2)}</TableCell>
                    <TableCell>{percentageOfPortfolio.toFixed(2)}%</TableCell>
                    <TableCell className="flex gap-2">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="ghost" size="icon"><Edit className="h-4 w-4" /></Button>
                        </DialogTrigger>
                        <HoldingDialog holding={holding} tickerName={ticker} />
                      </Dialog>
                      <Button variant="ghost" size="icon" onClick={() => removeHolding(ticker)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

const PortfolioCharts = ({ holdings, tickerPrices }: { holdings: { [key: string]: Holding }, tickerPrices: { [key: string]: number }}) => {
  // Morandi color palette
  const COLORS = ['#D4B2A7', '#7B92A6', '#A5A890', '#BDBAAE', '#C48A69', '#E8D5A2'];

  const tickerData = Object.entries(holdings).map(([ticker, holding]) => ({
    name: ticker,
    value: (tickerPrices[ticker] || 0) * holding.shares,
  })).filter(item => item.value > 0);

  const categoryMapping: { [key: string]: string } = {
    'AAPL': 'Growth',
    'MSFT': 'Dividend',
    'TSLA': 'Speculative',
    'GOOGL': 'Growth'
  };

  const categoryData = Object.entries(holdings).reduce((acc, [ticker, holding]) => {
    const category = categoryMapping[ticker] || 'Other';
    const value = (tickerPrices[ticker] || 0) * holding.shares;
    const existing = acc.find(item => item.name === category);
    if (existing) {
      existing.value += value;
    } else {
      acc.push({ name: category, value });
    }
    return acc;
  }, [] as { name: string; value: number }[]).filter(item => item.value > 0);

  const renderCustomizedLabel = (props: any) => {
    const { cx, cy, midAngle, innerRadius, outerRadius, percent } = props;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * (Math.PI / 180));
    const y = cy + radius * Math.sin(-midAngle * (Math.PI / 180));

    return (
      <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" className="text-xs font-bold">
        {`${(percent * 100).toFixed(1)}%`}
      </text>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio Allocation</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-8 h-80">
        <div className="w-full h-full">
          <h3 className="text-center font-semibold mb-2">By Ticker</h3>
          <ResponsiveContainer>
            <PieChart>
              <Pie data={tickerData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} fill="#8884d8" labelLine={false} label={renderCustomizedLabel}>
                {tickerData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="w-full h-full">
          <h3 className="text-center font-semibold mb-2">By Category</h3>
          <ResponsiveContainer>
            <PieChart>
              <Pie data={categoryData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} fill="#82ca9d" labelLine={false} label={renderCustomizedLabel}>
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

// --- Main Portfolio Component ---

export const Portfolio = () => {
  const { holdings, removeHolding, totalAssets, setTotalAssets } = useTickerStore();
  const [tickerPrices, setTickerPrices] = useState<{ [key: string]: number }>({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchPrices = async () => {
      setIsLoading(true);
      const tickers = Object.keys(holdings);
      if (tickers.length === 0) {
        setIsLoading(false);
        return;
      }
      const pricePromises = tickers.map(ticker =>
        fetch(`${API_BASE_URL}/api/v1/stock/${ticker}/price`).then(res => res.json())
      );

      try {
        const results = await Promise.all(pricePromises);
        const prices: { [key: string]: number } = {};
        results.forEach(result => {
          if (result.ticker && result.currentPrice) {
            prices[result.ticker] = result.currentPrice;
          }
        });
        setTickerPrices(prices);
      } catch (error) {
        console.error("Failed to fetch ticker prices:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPrices();
  }, [holdings]);

  const totalPortfolioValue = Object.entries(holdings).reduce((acc, [ticker, holding]) => {
    const currentPrice = tickerPrices[ticker] || 0;
    return acc + holding.shares * currentPrice;
  }, 0);

  return (
    <div className="space-y-6">
      <PortfolioSummary 
        value={totalPortfolioValue} 
        totalAssets={totalAssets} 
        setTotalAssets={setTotalAssets} 
      />
      <HoldingsTable 
        holdings={holdings} 
        tickerPrices={tickerPrices} 
        removeHolding={removeHolding} 
      />
      <PortfolioCharts 
        holdings={holdings} 
        tickerPrices={tickerPrices} 
      />
    </div>
  );
};
