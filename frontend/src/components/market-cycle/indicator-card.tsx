"use client";

import { useTranslations } from "next-intl";

interface IndicatorCardProps {
    name: string;
    value: number | null;
    secondary_value?: number | null;
    status: string;
    description: string;
}

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

export function IndicatorCard({ name, value, secondary_value, status, description }: IndicatorCardProps) {
    const t = useTranslations("MarketCycle");

    const statusColor = STATUS_COLORS[status] || STATUS_COLORS.Unknown;

    const formatValue = (val: number | null, indicatorName: string): string => {
        if (val === null) return "N/A";

        // Format based on indicator type
        if (indicatorName === "Trend") {
            return val.toLocaleString(undefined, { maximumFractionDigits: 0 });
        }
        if (indicatorName === "Recession") {
            return `${val >= 0 ? "+" : ""}${val.toFixed(2)}%`;
        }
        if (indicatorName === "Breadth") {
            return val.toFixed(0);
        }
        return val.toFixed(2);
    };

    // Display format for indicators with two values
    const displayValue = () => {
        if (secondary_value !== undefined && secondary_value !== null) {
            return `${formatValue(value, name)} / ${formatValue(secondary_value, name)}`;
        }
        return formatValue(value, name);
    };

    return (
        <div className="p-4 rounded-lg bg-muted/50">
            <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">{t(`indicator_${name.toLowerCase()}`)}</span>
                <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${statusColor}`}
                >
                    {status}
                </span>
            </div>
            <div className="text-lg font-bold mb-1">{displayValue()}</div>
            <p className="text-xs text-muted-foreground">{description}</p>
        </div>
    );
}

interface IndicatorCardsProps {
    indicators: Array<{
        name: string;
        value: number | null;
        secondary_value?: number | null;
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
                    secondary_value={indicator.secondary_value}
                    status={indicator.status}
                    description={indicator.description}
                />
            ))}
        </div>
    );
}
