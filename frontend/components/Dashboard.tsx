'use client';

import React, { useEffect, useState } from 'react';
import { useTickerStore } from '@/store/tickerStore';
import CandlestickChart, { CandlestickData } from './CandlestickChart';
import MACDChart from './MACDChart';
import VolumeChart from './VolumeChart';
import { Switch } from './ui/switch';
import { Label } from './ui/label';

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
  PEratio?: number;
  dividendYield?: number;
}

interface ApiKlineData {
  Date: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
  UpperBand?: number | null;
  MiddleBand?: number | null;
  LowerBand?: number | null;
  MA7?: number | null;
  MA30?: number | null;
  MA90?: number | null;
  EMA5?: number | null;
  EMA10?: number | null;
  EMA20?: number | null;
  MACD_line?: number | null;
  Signal_line?: number | null;
  MACD_histogram?: number | null;
}

const API_BASE_URL = 'http://localhost:8000';

const Dashboard = () => {
  const { selectedTicker } = useTickerStore();

  const [priceData, setPriceData] = useState<PriceData | null>(null);
  const [klineData, setKlineData] = useState<CandlestickData[]>([]);
  const [levels, setLevels] = useState<{ [key: string]: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBands, setShowBands] = useState(false);
  const [showMA, setShowMA] = useState(false);
  const [showEMA, setShowEMA] = useState(false);
  const [showMACD, setShowMACD] = useState(true);
  const [showVolume, setShowVolume] = useState(true);
  const [showLevels, setShowLevels] = useState(false);

  useEffect(() => {
    if (!selectedTicker) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [priceResponse, klineResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/api/v1/stock/${selectedTicker}/price`),
          fetch(`${API_BASE_URL}/api/v1/stock/${selectedTicker}/kline?period=1y&interval=1d`), // Fetch 1 year for better indicator accuracy
        ]);

        if (!priceResponse.ok || !klineResponse.ok) {
          throw new Error('Failed to fetch data');
        }

        const price = await priceResponse.json();
        const klineFullData = await klineResponse.json();
        const kline: ApiKlineData[] = klineFullData.kline_data;
        const supportResistanceLevels = klineFullData.levels;

        const formattedKlineData = kline.map(d => ({
          time: d.Date,
          open: d.Open,
          high: d.High,
          low: d.Low,
          close: d.Close,
          Volume: d.Volume,
          UpperBand: d.UpperBand,
          MiddleBand: d.MiddleBand,
          LowerBand: d.LowerBand,
          MA7: d.MA7,
          MA30: d.MA30,
          MA90: d.MA90,
          EMA5: d.EMA5,
          EMA10: d.EMA10,
          EMA20: d.EMA20,
          MACD_line: d.MACD_line,
          Signal_line: d.Signal_line,
          MACD_histogram: d.MACD_histogram,
        }));

        setPriceData(price);
        setKlineData(formattedKlineData);
        setLevels(supportResistanceLevels);

      } catch (err) {
        if (err instanceof Error) setError(err.message);
        else setError('An unknown error occurred');
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
        <div className="p-4 border rounded-lg"><div className="text-sm text-muted-foreground">Price</div><div className="text-2xl font-bold">{priceData?.currentPrice?.toFixed(2) || 'N/A'}</div></div>
        <div className="p-4 border rounded-lg"><div className="text-sm text-muted-foreground">Open</div><div className="text-2xl font-bold">{priceData?.open?.toFixed(2) || 'N/A'}</div></div>
        <div className="p-4 border rounded-lg"><div className="text-sm text-muted-foreground">High</div><div className="text-2xl font-bold">{priceData?.dayHigh?.toFixed(2) || 'N/A'}</div></div>
        <div className="p-4 border rounded-lg"><div className="text-sm text-muted-foreground">Low</div><div className="text-2xl font-bold">{priceData?.dayLow?.toFixed(2) || 'N/A'}</div></div>
        <div className="p-4 border rounded-lg"><div className="text-sm text-muted-foreground">Market Cap</div><div className="text-2xl font-bold">{((priceData?.marketCap || 0) / 1_000_000_000_000).toFixed(2) || 'N/A'} T</div></div>
        <div className="p-4 border rounded-lg"><div className="text-sm text-muted-foreground">Volume</div><div className="text-2xl font-bold">{((priceData?.volume || 0) / 1_000_000).toFixed(2) || 'N/A'} M</div></div>
        <div className="p-4 border rounded-lg"><div className="text-sm text-muted-foreground">PE Ratio</div><div className="text-2xl font-bold">{priceData?.PEratio?.toFixed(2) || 'N/A'}</div></div>
        <div className="p-4 border rounded-lg"><div className="text-sm text-muted-foreground">Dividend Yield</div><div className="text-2xl font-bold">{priceData?.dividendYield ? `${priceData.dividendYield.toFixed(2)} %` : 'N/A'}</div></div>
      </div>

      {/* Chart Section */}
      <div className="w-full">
        <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
          <h2 className="text-xl font-semibold">Price Chart</h2>
          <div className="flex items-center space-x-4 flex-wrap gap-2">
            <div className="flex items-center space-x-2"><Switch id="volume-toggle" checked={showVolume} onCheckedChange={setShowVolume} /><Label htmlFor="volume-toggle">Volume</Label></div>
            <div className="flex items-center space-x-2"><Switch id="macd-toggle" checked={showMACD} onCheckedChange={setShowMACD} /><Label htmlFor="macd-toggle">MACD</Label></div>
            <div className="flex items-center space-x-2"><Switch id="ma-toggle" checked={showMA} onCheckedChange={setShowMA} /><Label htmlFor="ma-toggle">MA</Label></div>
            <div className="flex items-center space-x-2"><Switch id="ema-toggle" checked={showEMA} onCheckedChange={setShowEMA} /><Label htmlFor="ema-toggle">EMA</Label></div>
            <div className="flex items-center space-x-2"><Switch id="bb-toggle" checked={showBands} onCheckedChange={setShowBands} /><Label htmlFor="bb-toggle">BBands</Label></div>
            <div className="flex items-center space-x-2"><Switch id="levels-toggle" checked={showLevels} onCheckedChange={setShowLevels} /><Label htmlFor="levels-toggle">S/R</Label></div>
          </div>
        </div>
        <div className="h-[450px]">
          <CandlestickChart 
            data={klineData} 
            ticker={selectedTicker} 
            showBands={showBands} 
            showMA={showMA}
            showEMA={showEMA}
            levels={levels}
            showLevels={showLevels}
          />
        </div>
        {showVolume && (
          <div className="mt-1">
            <VolumeChart data={klineData} height={100} />
          </div>
        )}
        {showMACD && (
          <div className="mt-1">
            <MACDChart data={klineData} height={150} />
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;