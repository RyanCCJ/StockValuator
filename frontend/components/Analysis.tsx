'use client';

import { useEffect } from 'react';
import { useTickerStore } from '../store/tickerStore';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Skeleton } from './ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import { Terminal, Info } from 'lucide-react';
import { EtfView } from './EtfView'; // Import the new ETF view

// Reusable Score Card Component for stocks
const ScoreCard = ({ title, score, breakdown }: { title: string; score: number; breakdown: { [key: string]: number | string } }) => (
  <Card>
    <CardHeader>
      <CardTitle className="flex justify-between items-center">
        <span>{title}</span>
        <span className="text-2xl font-bold text-primary">{score.toFixed(1)}</span>
      </CardTitle>
      <CardDescription>Based on fundamental analysis</CardDescription>
    </CardHeader>
    <CardContent>
      <div className="space-y-2">
        {Object.entries(breakdown).map(([key, value]) => (
          <div key={key} className="flex justify-between text-sm">
            <span className="text-muted-foreground">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
            <span className="font-medium">{typeof value === 'number' ? value.toFixed(1) : value}</span>
          </div>
        ))}
      </div>
    </CardContent>
  </Card>
);

// Reusable Fair Value Item Component for stocks
const FairValueItem = ({ title, data }: { title: string; data: { value: number | null; reason: string } }) => (
  <div className="p-4 rounded-lg bg-secondary">
    <div className="flex items-center justify-center text-sm text-muted-foreground mb-1">
      <span>{title}</span>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Info className="h-3 w-3 ml-1.5 cursor-pointer" />
          </TooltipTrigger>
          <TooltipContent>
            <p>{data.reason}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
    <p className="text-2xl font-bold">
      {data.value ? `$${data.value.toFixed(2)}` : 'N/A'}
    </p>
  </div>
);

// Component for displaying stock-specific analysis
interface StockAnalysisData {
  ticker: string;
  analysis_scores: {
    confidence: {
      total_score: number;
      breakdown: { [key: string]: number | string };
    };
    dividend: {
      total_score: number;
      breakdown: { [key: string]: number | string };
    };
    value: {
      total_score: number;
      breakdown: { [key: string]: number | string };
    };
  };
  fair_value: {
    growth_value: { value: number | null; reason: string };
    dividend_value: { value: number | null; reason: string };
    asset_value: { value: number | null; reason: string };
  };
}

const StockAnalysisView = ({ data }: { data: StockAnalysisData }) => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold">Fundamental Analysis for {data.ticker}</h2>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <ScoreCard 
        title="Confidence Score"
        score={data.analysis_scores.confidence.total_score}
        breakdown={data.analysis_scores.confidence.breakdown}
      />
      <ScoreCard 
        title="Dividend Score"
        score={data.analysis_scores.dividend.total_score}
        breakdown={data.analysis_scores.dividend.breakdown}
      />
      <ScoreCard 
        title="Value Score"
        score={data.analysis_scores.value.total_score}
        breakdown={data.analysis_scores.value.breakdown}
      />
    </div>
    <div>
      <h3 className="text-xl font-bold mb-4">Fair Value Estimation</h3>
      <Card>
        <CardContent className="pt-6 grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
          <FairValueItem title="Growth Value" data={data.fair_value.growth_value} />
          <FairValueItem title="Dividend Value" data={data.fair_value.dividend_value} />
          <FairValueItem title="Asset Value" data={data.fair_value.asset_value} />
        </CardContent>
      </Card>
    </div>
  </div>
);

// Main Analysis Component
export const Analysis = () => {
  const {
    selectedTicker,
    analysisData,
    isLoading,
    error,
    fetchAnalysis,
  } = useTickerStore();

  useEffect(() => {
    if (selectedTicker) {
      fetchAnalysis(selectedTicker);
    }
  }, [selectedTicker, fetchAnalysis]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-1/2 mb-4" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </CardHeader>
              <CardContent className="space-y-2">
                {[...Array(5)].map((_, j) => (
                  <div key={j} className="flex justify-between">
                    <Skeleton className="h-4 w-1/3" />
                    <Skeleton className="h-4 w-1/4" />
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <Terminal className="h-4 w-4" />
        <AlertTitle>Error Fetching Data</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!analysisData) {
    return <div className="text-center text-muted-foreground">Select a ticker to see the analysis.</div>;
  }

  // Conditionally render based on the quote type
  if (analysisData.quoteType === 'ETF') {
    return <EtfView data={analysisData.data} />;
  }

  if (analysisData.quoteType === 'EQUITY') {
    return <StockAnalysisView data={analysisData.data} />;
  }

  return <div className="text-center text-muted-foreground">Unsupported quote type.</div>;
};
