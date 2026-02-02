"use client";

import { useTranslations } from "next-intl";

interface PhaseGaugeProps {
    phase: string;
    phaseNumber: number;
    riskLevel: string;
    totalScore: number;
}

const PHASE_COLORS = {
    1: "from-green-500 to-green-600",     // Accumulation
    2: "from-blue-500 to-blue-600",       // Mark-Up
    3: "from-yellow-500 to-yellow-600",   // Distribution
    4: "from-red-500 to-red-600",         // Mark-Down
};

const PHASE_BG_COLORS = {
    1: "bg-green-100 dark:bg-green-900/30",
    2: "bg-blue-100 dark:bg-blue-900/30",
    3: "bg-yellow-100 dark:bg-yellow-900/30",
    4: "bg-red-100 dark:bg-red-900/30",
};

const RISK_COLORS = {
    Low: "text-green-600 dark:text-green-400",
    Medium: "text-yellow-600 dark:text-yellow-400",
    High: "text-red-600 dark:text-red-400",
    Unknown: "text-gray-500",
};

export function PhaseGauge({ phase, phaseNumber, riskLevel, totalScore }: PhaseGaugeProps) {
    const t = useTranslations("MarketCycle");

    // Calculate the gauge rotation angle (0-100 maps to -90 to 90 degrees)
    const rotation = ((totalScore / 100) * 180) - 90;

    // Phase segments for the gauge
    const phases = [
        { number: 1, label: t("phase_accumulation"), shortLabel: "1" },
        { number: 2, label: t("phase_markup"), shortLabel: "2" },
        { number: 3, label: t("phase_distribution"), shortLabel: "3" },
        { number: 4, label: t("phase_markdown"), shortLabel: "4" },
    ];

    return (
        <div className="flex flex-col items-center p-6">
            {/* Gauge Container */}
            <div className="relative w-64 h-32 mb-4">
                {/* Semi-circle gauge background */}
                <div className="absolute inset-0 overflow-hidden">
                    <div
                        className="w-64 h-64 rounded-full border-8 border-gray-200 dark:border-gray-700"
                        style={{ clipPath: "inset(50% 0 0 0)" }}
                    />
                </div>

                {/* Phase segments */}
                <div className="absolute inset-0 overflow-hidden">
                    {/* Phase 4 (left) - Mark-Down (red) */}
                    <div
                        className="absolute w-64 h-64 rounded-full border-8 border-red-500"
                        style={{
                            clipPath: "polygon(0 50%, 25% 0, 25% 50%)",
                        }}
                    />
                    {/* Phase 1 - Accumulation (green) */}
                    <div
                        className="absolute w-64 h-64 rounded-full border-8 border-green-500"
                        style={{
                            clipPath: "polygon(25% 50%, 25% 0, 50% 0, 50% 50%)",
                        }}
                    />
                    {/* Phase 2 - Mark-Up (blue) */}
                    <div
                        className="absolute w-64 h-64 rounded-full border-8 border-blue-500"
                        style={{
                            clipPath: "polygon(50% 50%, 50% 0, 75% 0, 75% 50%)",
                        }}
                    />
                    {/* Phase 3 (right) - Distribution (yellow) */}
                    <div
                        className="absolute w-64 h-64 rounded-full border-8 border-yellow-500"
                        style={{
                            clipPath: "polygon(75% 50%, 75% 0, 100% 0, 100% 50%)",
                        }}
                    />
                </div>

                {/* Gauge needle */}
                <div
                    className="absolute bottom-0 left-1/2 origin-bottom"
                    style={{
                        transform: `translateX(-50%) rotate(${rotation}deg)`,
                        transition: "transform 0.5s ease-out",
                    }}
                >
                    <div className="w-1 h-24 bg-gray-800 dark:bg-white rounded-full" />
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-4 bg-gray-800 dark:bg-white rounded-full" />
                </div>

                {/* Score display in center */}
                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-center">
                    <div className="text-3xl font-bold">{totalScore}</div>
                    <div className="text-xs text-muted-foreground">{t("score")}</div>
                </div>
            </div>

            {/* Phase labels below gauge */}
            <div className="flex justify-between w-64 text-xs text-muted-foreground mb-4">
                <span>0</span>
                <span>50</span>
                <span>100</span>
            </div>

            {/* Current Phase Info */}
            <div className={`rounded-lg px-6 py-4 text-center ${PHASE_BG_COLORS[phaseNumber as keyof typeof PHASE_BG_COLORS] || "bg-gray-100 dark:bg-gray-800"}`}>
                <div className="text-sm text-muted-foreground mb-1">{t("current_phase")}</div>
                <div className="text-xl font-bold mb-2">
                    {t("phase_prefix")} {phaseNumber}: {phase}
                </div>
                <div className="flex items-center justify-center gap-2">
                    <span className="text-sm">{t("risk_level")}:</span>
                    <span className={`font-semibold ${RISK_COLORS[riskLevel as keyof typeof RISK_COLORS] || RISK_COLORS.Unknown}`}>
                        {riskLevel}
                    </span>
                </div>
            </div>

            {/* Phase Legend */}
            <div className="mt-6 grid grid-cols-4 gap-2 text-xs">
                {phases.map((p) => (
                    <div
                        key={p.number}
                        className={`text-center p-2 rounded ${
                            p.number === phaseNumber
                                ? "ring-2 ring-offset-2 ring-primary"
                                : ""
                        }`}
                    >
                        <div
                            className={`w-3 h-3 rounded-full mx-auto mb-1 bg-gradient-to-r ${
                                PHASE_COLORS[p.number as keyof typeof PHASE_COLORS]
                            }`}
                        />
                        <div className="font-medium">{p.shortLabel}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}
