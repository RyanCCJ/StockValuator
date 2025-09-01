'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Type definitions for the component's data prop
interface EtfHolding {
  symbol: string;
  name: string;
  weight: string;
}

interface EtfData {
  details: any; // Contains summary and all key metrics from yfinance
  top_holdings: EtfHolding[];
}

const COLORS = ['#D4B2A7', '#7B92A6', '#A5A890', '#BDBAAE', '#C48A69', '#E8D5A2', '#9B7C6D', '#A9C4D4', '#D9E3C8', '#EFEBE0', '#A39187', '#B7C9D6', '#CAD0B8', '#D1C9B9', '#D4A68A'];
const OTHERS_COLOR = '#9ca3af'; // A neutral grey for the 'Others' slice

const renderCustomizedLabel = (props: any) => {
  const { percent } = props;
  if (percent < 0.05) return null; // Don't render labels for very small slices
  return `${(percent * 100).toFixed(1)}%`;
};

// Helper to format keys from camelCase to Title Case
const formatKey = (key: string) => {
  const result = key.replace(/([A-Z])/g, " $1");
  return result.charAt(0).toUpperCase() + result.slice(1);
};

export const EtfView = ({ data }: { data: EtfData }) => {
  const topHoldingsData = data.top_holdings.map(h => ({
    name: h.symbol,
    value: parseFloat(h.weight.replace('%', '')),
    fullName: h.name
  }));

  const topHoldingsValue = topHoldingsData.reduce((acc, curr) => acc + curr.value, 0);
  
  const chartData = [...topHoldingsData];
  if (topHoldingsValue < 100 && topHoldingsValue > 0) {
    chartData.push({ name: 'Others', value: 100 - topHoldingsValue, fullName: 'Other Holdings' });
  }

  // Filter and format key metrics for display
  const keyMetrics = Object.entries(data.details || {}).filter(([key, value]) => 
    value !== null && value !== undefined && ['fundFamily', 'expenseRatio', 'trailingPE', 'dividendYield', 'fiveYearAverageReturn', 'beta'].includes(key)
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>ETF Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {data.details?.longBusinessSummary || 'No summary available.'}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Key Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-2">
            {keyMetrics.length > 0 ? keyMetrics.map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm border-b py-1">
                <span className="font-medium">{formatKey(key)}</span>
                <span>{value}</span>
              </div>
            )) : <p className="text-sm text-muted-foreground">No key metrics available.</p>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top 15 Holdings</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
          <div className="w-full">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Holding</TableHead>
                  <TableHead className="text-right">Assets</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {topHoldingsData.map((holding) => (
                  <TableRow key={holding.name}>
                    <TableCell className="font-medium">{holding.name}</TableCell>
                    <TableCell>{holding.fullName}</TableCell>
                    <TableCell className="text-right">{holding.value.toFixed(2)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <div className="w-full h-96">
            <ResponsiveContainer>
              <PieChart>
                <Pie 
                  data={chartData} 
                  dataKey="value" 
                  nameKey="name" 
                  cx="50%" 
                  cy="50%" 
                  outerRadius={120} 
                  labelLine={false}
                  label={renderCustomizedLabel}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.name === 'Others' ? OTHERS_COLOR : COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number, name: string) => [`${value.toFixed(2)}%`, name]} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
