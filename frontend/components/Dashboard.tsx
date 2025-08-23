'use client';

import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useTickerStore } from '@/store/tickerStore';

// Define types for our data
interface PriceData {
  ticker: string;
  currentPrice?: number;
  open?: number;
  dayHigh?: number;
  dayLow?: number;
  previousClose?: number;
  volume?: number;
  marketCap?: number;
}

interface KlineData {
  Date: string;
  Close: number;
}

const API_BASE_URL = 'http://localhost:8000';

const Dashboard = () => {
  // Use the global state instead of local state for the ticker
  const { selectedTicker } = useTickerStore();

  const [priceData, setPriceData] = useState<PriceData | null>(null);
  const [klineData, setKlineData] = useState<KlineData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // useEffect now depends on the global selectedTicker
  useEffect(() => {
    if (!selectedTicker) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [priceResponse, klineResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/stock/${selectedTicker}/price`),
          fetch(`${API_BASE_URL}/stock/${selectedTicker}/kline?period=6mo&interval=1d`),
        ]);

        if (!priceResponse.ok) {
          const errorData = await priceResponse.json();
          throw new Error(errorData.detail || `Failed to fetch price data for ${selectedTicker}`);
        }
        if (!klineResponse.ok) {
          const errorData = await klineResponse.json();
          throw new Error(errorData.detail || `Failed to fetch kline data for ${selectedTicker}`);
        }

        const price = await priceResponse.json();
        const kline = await klineResponse.json();

        setPriceData(price);
        setKlineData(kline);

      } catch (err: any) {
        setError(err.message);
        setPriceData(null);
        setKlineData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedTicker]); // Dependency array updated to global state

  if (loading) {
    return <div>Loading dashboard for {selectedTicker}...</div>;
  }

  if (error) {
    return <div className="text-destructive">Error: {error}</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">{priceData?.ticker || selectedTicker} Dashboard</h1>
      
      {/* Price Info Section */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 border rounded-lg">
          <div className="text-sm text-muted-foreground">Price</div>
          <div className="text-2xl font-bold">{priceData?.currentPrice?.toFixed(2) || 'N/A'}</div>
        </div>
        <div className="p-4 border rounded-lg">
          <div className="text-sm text-muted-foreground">Open</div>
          <div className="text-2xl font-bold">{priceData?.open?.toFixed(2) || 'N/A'}</div>
        </div>
        <div className="p-4 border rounded-lg">
          <div className="text-sm text-muted-foreground">High</div>
          <div className="text-2xl font-bold">{priceData?.dayHigh?.toFixed(2) || 'N/A'}</div>
        </div>
        <div className="p-4 border rounded-lg">
          <div className="text-sm text-muted-foreground">Low</div>
          <div className="text-2xl font-bold">{priceData?.dayLow?.toFixed(2) || 'N/A'}</div>
        </div>
        <div className="p-4 border rounded-lg col-span-2">
          <div className="text-sm text-muted-foreground">Market Cap</div>
          <div className="text-2xl font-bold">{((priceData?.marketCap || 0) / 1_000_000_000_000).toFixed(2) || 'N/A'} T</div>
        </div>
        <div className="p-4 border rounded-lg col-span-2">
          <div className="text-sm text-muted-foreground">Volume</div>
          <div className="text-2xl font-bold">{((priceData?.volume || 0) / 1_000_000).toFixed(2) || 'N/A'} M</div>
        </div>
      </div>

      {/* Chart Section */}
      <div className="h-[400px] w-full">
        <h2 className="text-xl font-semibold mb-2">6-Month Price Chart</h2>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={klineData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="Date" />
            <YAxis domain={['dataMin', 'dataMax']} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="Close" stroke="#8884d8" activeDot={{ r: 8 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default Dashboard;