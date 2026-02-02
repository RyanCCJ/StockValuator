"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    TrendingUp,
    TrendingDown,
    DollarSign,
    Activity,
    BarChart3,
    AlertTriangle,
} from "lucide-react";

interface IndicatorCardProps {
    name: string;
    value: number | null;
    status: string;
    description: string;
}

const INDICATOR_ICONS: Record<string, React.ReactNode> = {
    Trend: <TrendingUp className="h-5 w-5" />,
    Valuation: <DollarSign className="h-5 w-5" />,
    Recession: <Activity className="h-5 w-5" />,
    Fear: <AlertTriangle className="h-5 w-5" />,
    Breadth: <BarChart3 className="h-5 w-5" />,
};

const STATUS_COLORS: Record<string, string> = {
    // Positive statuses
    Bullish: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    Undervalued: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    Normal: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    Improving: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",

    // Neutral statuses
    Fair: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
    Flat: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",

    // Negative statuses
    Bearish: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    Overvalued: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    Inverted: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    "High Fear": "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
    Complacent: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    Weakening: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",

    // Unknown
    Unknown: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
};

export function IndicatorCard({ name, value, status, description }: IndicatorCardProps) {
    const t = useTranslations("MarketCycle");

    const icon = INDICATOR_ICONS[name] || <Activity className="h-5 w-5" />;
    const statusColor = STATUS_COLORS[status] || STATUS_COLORS.Unknown;

    const formatValue = (val: number | null): string => {
        if (val === null) return "N/A";

        // Format based on indicator type
        if (name === "Trend") {
            return val.toLocaleString(undefined, { maximumFractionDigits: 0 });
        }
        if (name === "Recession") {
            return `${val >= 0 ? "+" : ""}${val.toFixed(2)}%`;
        }
        return val.toFixed(2);
    };

    return (
        <Card className="relative overflow-hidden">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="p-2 rounded-lg bg-muted">{icon}</div>
                        <CardTitle className="text-sm font-medium">{t(`indicator_${name.toLowerCase()}`)}</CardTitle>
                    </div>
                    <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${statusColor}`}
                    >
                        {status}
                    </span>
                </div>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold mb-1">{formatValue(value)}</div>
                <p className="text-xs text-muted-foreground">{description}</p>
            </CardContent>
        </Card>
    );
}

interface IndicatorCardsProps {
    indicators: Array<{
        name: string;
        value: number | null;
        status: string;
        description: string;
    }>;
}

export function IndicatorCards({ indicators }: IndicatorCardsProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {indicators.map((indicator) => (
                <IndicatorCard
                    key={indicator.name}
                    name={indicator.name}
                    value={indicator.value}
                    status={indicator.status}
                    description={indicator.description}
                />
            ))}
        </div>
    );
}
