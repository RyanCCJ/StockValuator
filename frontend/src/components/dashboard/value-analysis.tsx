"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { FundamentalDataResponse, InstitutionalHolder, TopHolding, SectorWeighting } from "@/services/api";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

interface ValueAnalysisProps {
    data: FundamentalDataResponse;
}

// romaO scientific color map - low saturation palette
const COLORS = [
    "#7E6B8F", // Muted Purple
    "#88A0A8", // Muted Teal
    "#9DB17C", // Muted Green
    "#C4A35A", // Muted Gold
    "#D49A6A", // Muted Orange
    "#C88B8B", // Muted Rose
    "#8B8BAD", // Muted Lavender
    "#7BA393", // Muted Sage
    "#B39B7A", // Muted Tan
    "#9A8F8F", // Muted Gray
    "#A89B78", // Muted Olive
];

// Custom tooltip for pie chart - theme aware
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const SectorTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        const data = payload[0];
        return (
            <div className="rounded-lg border bg-popover/95 px-3 py-2 text-popover-foreground shadow-xl backdrop-blur-sm">
                <div className="font-semibold">{data.name}</div>
                <div className="text-sm opacity-80">{data.value.toFixed(2)}%</div>
            </div>
        );
    }
    return null;
};

function formatNumber(value: number | null | undefined, decimals: number = 2): string {
    if (value === null || value === undefined) return "N/A";
    return value.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
}

function formatPercent(value: number | null | undefined): string {
    if (value === null || value === undefined) return "N/A";
    return `${(value * 100).toFixed(2)}%`;
}

// For values that are already in percentage form (e.g., dividendYield from yfinance)
function formatRawPercent(value: number | null | undefined): string {
    if (value === null || value === undefined) return "N/A";
    return `${value.toFixed(2)}%`;
}

function formatMarketCap(value: number | null | undefined): string {
    if (value === null || value === undefined) return "N/A";
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toLocaleString()}`;
}

// Analyst Rating bar component (internal helper)
function AnalystRatingBar({ rating }: { rating: string | null | undefined }) {
    if (!rating) return null;

    // Parse rating like "1.3 - Strong Buy"
    const match = rating.match(/^([\d.]+)\s*-\s*(.+)$/);
    if (!match) return <span>{rating}</span>;

    const score = parseFloat(match[1]);
    const label = match[2];

    // Score ranges: 1 = Strong Buy, 2 = Buy, 3 = Hold, 4 = Sell, 5 = Strong Sell
    const percentage = ((5 - score) / 4) * 100;

    // Color based on score
    const getColor = (score: number) => {
        if (score <= 1.5) return "bg-green-500";
        if (score <= 2.5) return "bg-lime-500";
        if (score <= 3.5) return "bg-yellow-500";
        if (score <= 4.5) return "bg-orange-500";
        return "bg-red-500";
    };

    return (
        <div className="space-y-2">
            <div className="flex justify-between text-sm">
                <span>Strong Sell</span>
                <span className="font-semibold">{label}</span>
                <span>Strong Buy</span>
            </div>
            <div className="h-3 bg-muted rounded-full overflow-hidden">
                <div
                    className={`h-full ${getColor(score)} transition-all duration-300`}
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
}

// ============================================================
// EXPORTED SUB-COMPONENTS FOR FLEXIBLE PAGE COMPOSITION
// ============================================================

/**
 * CompanyHeader - Displays company name, logo, market cap, and description
 * For use in the "Company Info" tab
 */
export function CompanyHeader({ data }: { data: FundamentalDataResponse }) {
    const t = useTranslations("StockDetail");

    return (
        <Card>
            <CardHeader>
                <div className="flex items-start gap-6">
                    {/* Left: Name and basic info */}
                    <div className="flex items-center gap-4 flex-shrink-0">
                        {/* Logo: prefer coin_image_url for crypto, otherwise use Brandfetch ticker API */}
                        <img
                            src={data.coin_image_url || `https://cdn.brandfetch.io/ticker/${data.symbol}?c=${process.env.NEXT_PUBLIC_BRANDFETCH_CLIENT_ID || ''}`}
                            alt={data.symbol}
                            className="w-12 h-12 rounded-lg object-contain bg-muted"
                            onError={(e) => { e.currentTarget.style.display = 'none'; }}
                        />
                        <div>
                            <CardTitle>{data.long_name || data.symbol}</CardTitle>
                            <CardDescription>
                                {data.sector && data.industry && `${data.sector} • ${data.industry}`}
                                {data.sector && !data.industry && data.sector}
                            </CardDescription>
                            <p className="text-lg font-semibold mt-1">{formatMarketCap(data.market_cap)}</p>
                        </div>
                    </div>

                    {/* Right: Description (scrollable) */}
                    {data.description && (
                        <div className="flex-1 min-w-0 border-l pl-6">
                            <p className="text-xs text-muted-foreground uppercase mb-2">{t("description")}</p>
                            <div className="max-h-32 overflow-y-auto pr-2">
                                <p className="text-sm text-muted-foreground leading-relaxed">{data.description}</p>
                            </div>
                        </div>
                    )}
                </div>
            </CardHeader>
        </Card>
    );
}

/**
 * KeyStatistics - Displays key financial metrics (PE, EPS, yields, etc.)
 * For use in the "Value Analysis" tab
 */
export function KeyStatistics({ data }: { data: FundamentalDataResponse }) {
    const t = useTranslations("StockDetail");

    const mainStats = [
        { label: t("trailing_pe"), value: formatNumber(data.trailing_pe) },
        { label: t("forward_pe"), value: formatNumber(data.forward_pe) },
        { label: t("trailing_eps"), value: formatNumber(data.trailing_eps) },
        { label: t("forward_eps"), value: formatNumber(data.forward_eps) },
    ];

    const metrics = [
        { label: t("dividend_yield"), value: formatRawPercent(data.dividend_yield) },
        { label: t("payout_ratio"), value: formatPercent(data.payout_ratio) },
        { label: t("profit_margins"), value: formatPercent(data.profit_margins) },
        { label: t("revenue_growth"), value: formatPercent(data.revenue_growth) },
        { label: t("beta"), value: formatNumber(data.beta) },
        { label: t("book_value"), value: data.book_value ? `$${formatNumber(data.book_value)}` : "N/A" },
        { label: t("52w_high"), value: data.fifty_two_week_high ? `$${formatNumber(data.fifty_two_week_high)}` : "N/A" },
        { label: t("52w_low"), value: data.fifty_two_week_low ? `$${formatNumber(data.fifty_two_week_low)}` : "N/A" },
    ];

    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-lg">{t("key_statistics")}</CardTitle>
                <CardDescription>
                    {t("last_updated")}: {new Date(data.last_updated).toLocaleString()}
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* PE & EPS */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {mainStats.map((stat) => (
                        <div key={stat.label} className="text-center p-4 bg-muted/50 rounded-lg">
                            <div className="text-sm text-muted-foreground">{stat.label}</div>
                            <div className="text-xl font-semibold mt-1">{stat.value}</div>
                        </div>
                    ))}
                </div>

                {/* Other Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {metrics.map((stat) => (
                        <div key={stat.label} className="text-center p-4 bg-muted/50 rounded-lg">
                            <div className="text-sm text-muted-foreground">{stat.label}</div>
                            <div className="text-xl font-semibold mt-1">{stat.value}</div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}

/**
 * AnalystRatingCard - Displays the analyst rating with visual bar
 * For use in the "Value Analysis" tab
 */
export function AnalystRatingCard({ data }: { data: FundamentalDataResponse }) {
    const t = useTranslations("StockDetail");

    if (!data.analyst_rating) return null;

    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-lg">{t("analyst_rating")}</CardTitle>
                <CardDescription>{t("analyst_rating_disclaimer")}</CardDescription>
            </CardHeader>
            <CardContent>
                <AnalystRatingBar rating={data.analyst_rating} />
            </CardContent>
        </Card>
    );
}

/**
 * InstitutionalHoldersTable - Displays institutional holders data
 * For use in the "Company Info" tab
 */
export function InstitutionalHoldersTable({ data }: { data: FundamentalDataResponse }) {
    const t = useTranslations("StockDetail");

    if (!data.institutional_holders || data.institutional_holders.length === 0) return null;

    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-lg">{t("institutional_holders")}</CardTitle>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>{t("holder")}</TableHead>
                            <TableHead className="text-right">{t("percent")}</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.institutional_holders.map((holder: InstitutionalHolder, index: number) => (
                            <TableRow key={index}>
                                <TableCell className="font-medium">{holder.holder}</TableCell>
                                <TableCell className="text-right">
                                    {holder.percent ? `${holder.percent.toFixed(2)}%` : "N/A"}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
}

// ============================================================
// INTERNAL COMPONENTS (not exported, for backward compatibility)
// ============================================================

// Stock/Crypto View Component (internal, composed of exported sub-components)
function StockView({ data, t }: { data: FundamentalDataResponse; t: (key: string) => string }) {
    return (
        <div className="space-y-6">
            <CompanyHeader data={data} />
            <KeyStatistics data={data} />
            <AnalystRatingCard data={data} />
            <InstitutionalHoldersTable data={data} />
        </div>
    );
}

// ETF View Component
function ETFView({ data, t }: { data: FundamentalDataResponse; t: (key: string) => string }) {
    const stats = [
        { label: t("trailing_pe"), value: formatNumber(data.trailing_pe) },
        { label: t("dividend_yield"), value: formatRawPercent(data.dividend_yield) },
        { label: t("beta_3_year"), value: formatNumber(data.beta_3_year) },
        { label: t("52w_high"), value: data.fifty_two_week_high ? `$${formatNumber(data.fifty_two_week_high)}` : "N/A" },
        { label: t("52w_low"), value: data.fifty_two_week_low ? `$${formatNumber(data.fifty_two_week_low)}` : "N/A" },
    ];

    // Transform sector weightings for pie chart
    const chartData = data.sector_weightings?.map((sw: SectorWeighting) => ({
        name: sw.sector,
        value: sw.weight
    })) || [];

    return (
        <div className="space-y-6">
            {/* Header with Name, Market Cap, and Description */}
            <Card>
                <CardHeader>
                    <div className="flex items-start gap-6">
                        {/* Left: Name and basic info */}
                        <div className="flex-shrink-0">
                            <CardTitle>{data.long_name || data.symbol}</CardTitle>
                            <CardDescription>
                                {data.expense_ratio != null && `${t("expense_ratio")}: ${formatRawPercent(data.expense_ratio)}`}
                            </CardDescription>
                            {data.market_cap && (
                                <p className="text-lg font-semibold mt-1">{formatMarketCap(data.market_cap)}</p>
                            )}
                        </div>

                        {/* Right: Description (scrollable) */}
                        {data.description && (
                            <div className="flex-1 min-w-0 border-l pl-6">
                                <p className="text-xs text-muted-foreground uppercase mb-2">{t("description")}</p>
                                <div className="max-h-32 overflow-y-auto pr-2">
                                    <p className="text-sm text-muted-foreground leading-relaxed">{data.description}</p>
                                </div>
                            </div>
                        )}
                    </div>
                </CardHeader>
            </Card>

            {/* Key Metrics */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">{t("key_statistics")}</CardTitle>
                    <CardDescription>
                        {t("last_updated")}: {new Date(data.last_updated).toLocaleString()}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        {stats.map((stat) => (
                            <div key={stat.label} className="text-center p-4 bg-muted/50 rounded-lg">
                                <div className="text-sm text-muted-foreground">{stat.label}</div>
                                <div className="text-xl font-semibold mt-1">{stat.value}</div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Combined Top Holdings & Sector Weightings */}
            {(data.top_holdings && data.top_holdings.length > 0) || chartData.length > 0 ? (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">{t("top_holdings")}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {/* Left: Top Holdings */}
                            {data.top_holdings && data.top_holdings.length > 0 && (
                                <div className="space-y-4">
                                    <Table>
                                        <TableHeader>
                                            <TableRow>
                                                <TableHead>{t("symbol")}</TableHead>
                                                <TableHead>{t("name")}</TableHead>
                                                <TableHead className="text-right">{t("percent")}</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {data.top_holdings.map((holding: TopHolding, index: number) => (
                                                <TableRow key={index}>
                                                    <TableCell className="font-medium">{holding.symbol}</TableCell>
                                                    <TableCell>{holding.name}</TableCell>
                                                    <TableCell className="text-right">
                                                        {holding.percent.toFixed(2)}%
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            )}

                            {/* Right: Sector Weightings Pie Chart */}
                            {chartData.length > 0 && (
                                <div className="space-y-4 h-[400px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={chartData}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={60}
                                                outerRadius={100}
                                                paddingAngle={2}
                                                dataKey="value"
                                                labelLine={false}
                                            >
                                                {chartData.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip content={<SectorTooltip />} />
                                            <Legend
                                                layout="horizontal"
                                                verticalAlign="bottom"
                                                align="center"
                                                wrapperStyle={{ paddingTop: 20 }}
                                                formatter={(value) => <span className="text-foreground text-sm">{value}</span>}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            ) : null}
        </div>
    );
}

export function ValueAnalysis({ data }: ValueAnalysisProps) {
    const t = useTranslations("StockDetail");

    if (data.is_etf) {
        return <ETFView data={data} t={t} />;
    }

    return <StockView data={data} t={t} />;
}
