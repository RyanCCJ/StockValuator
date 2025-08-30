'use client';

import React, { useEffect, useState } from 'react';
import { useTickerStore } from '@/store/tickerStore';
import CandlestickChart, { CandlestickData } from './CandlestickChart';

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

interface ApiKlineData {
  Date: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
}

const API_BASE_URL = 'http://localhost:8000';

const Dashboard = () => {
  const { selectedTicker } = useTickerStore();

  const [priceData, setPriceData] = useState<PriceData | null>(null);
  const [klineData, setKlineData] = useState<CandlestickData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedTicker) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [priceResponse, klineResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/api/v1/stock/${selectedTicker}/price`),
          fetch(`${API_BASE_URL}/api/v1/stock/${selectedTicker}/kline?period=6mo&interval=1d`),
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
        const kline: ApiKlineData[] = await klineResponse.json();

        // Map the API data to the format required by the candlestick chart
        const formattedKlineData = kline.map(d => ({
          time: d.Date,
          open: d.Open,
          high: d.High,
          low: d.Low,
          close: d.Close,
        }));

        setPriceData(price);
        setKlineData(formattedKlineData);

      } catch (err: any) {
        setError(err.message);
        setPriceData(null);
        setKlineData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedTicker]);

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
      <div className="w-full h-[450px]">
        <h2 className="text-xl font-semibold mb-2">6-Month Price Chart</h2>
        <CandlestickChart data={klineData} ticker={selectedTicker} />
      </div>
    </div>
  );
};

export default Dashboard;
