"use client";

import { useTranslations } from "next-intl";

interface MarketCycleWaveProps {
    totalScore: number;
    sp500Price: number | null;
    sp500Ma200: number | null;
    phase: string;
    phaseNumber: number;
    riskLevel: string;
}

// Wave constants
const SVG_WIDTH = 520;
const SVG_HEIGHT = 240;
const WAVE_PADDING_LEFT = 55;
const WAVE_PADDING_RIGHT = 20;
const WAVE_PADDING_TOP = 30;
const WAVE_PADDING_BOTTOM = 50;
const WAVE_WIDTH = SVG_WIDTH - WAVE_PADDING_LEFT - WAVE_PADDING_RIGHT;
const WAVE_HEIGHT = SVG_HEIGHT - WAVE_PADDING_TOP - WAVE_PADDING_BOTTOM;
const WAVE_CENTER_Y = WAVE_PADDING_TOP + WAVE_HEIGHT / 2;
const WAVE_AMPLITUDE = WAVE_HEIGHT / 2 - 5;

// Zone boundaries - Traditional Wyckoff Cycle Order:
// Accumulation (valley/bottom) → Mark-Up (rising) → Distribution (peak/top) → Mark-Down (falling)
const ZONES = {
    accumulation: { start: 0, end: 0.15 },      // Valley/Bottom - starting point
    markUp: { start: 0.15, end: 0.40 },         // Rising phase
    distribution: { start: 0.40, end: 0.60 },   // Peak/Top
    markDown: { start: 0.60, end: 0.85 },       // Falling phase
};

// Phase colors
const PHASE_COLORS = {
    accumulation: { fill: "rgba(34, 197, 94, 0.2)", stroke: "#22c55e", text: "#4ade80" },
    markUp: { fill: "rgba(59, 130, 246, 0.2)", stroke: "#3b82f6", text: "#60a5fa" },
    distribution: { fill: "rgba(234, 179, 8, 0.2)", stroke: "#eab308", text: "#facc15" },
    markDown: { fill: "rgba(239, 68, 68, 0.2)", stroke: "#ef4444", text: "#f87171" },
};

const RISK_COLORS = {
    Low: "text-green-600 dark:text-green-400",
    Medium: "text-yellow-600 dark:text-yellow-400",
    High: "text-red-600 dark:text-red-400",
    Unknown: "text-gray-500",
};

/**
 * Get Y coordinate on the wave for a given t (0-1)
 * Wave starts at valley (Accumulation), rises to peak (Distribution), then falls
 * Using cosine so: t=0 is valley, t=0.5 is peak, t=1 is valley again
 */
function getWaveY(t: number): number {
    // Cosine wave: starts at bottom (valley), peaks in middle
    return WAVE_CENTER_Y + WAVE_AMPLITUDE * Math.cos(t * 2 * Math.PI);
}

/**
 * Generate the wave path
 */
function generateWavePath(): string {
    const points: string[] = [];
    const steps = 100;
    const endT = 0.85; // Show most of one cycle

    for (let i = 0; i <= steps; i++) {
        const t = (i / steps) * endT;
        const x = WAVE_PADDING_LEFT + (t / endT) * WAVE_WIDTH;
        const y = getWaveY(t);
        points.push(`${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`);
    }

    return points.join(" ");
}

/**
 * Generate a filled area path for a zone
 */
function generateZonePath(startT: number, endT: number): string {
    const points: string[] = [];
    const steps = 50;
    const visibleEnd = 0.85;

    const startX = WAVE_PADDING_LEFT + (startT / visibleEnd) * WAVE_WIDTH;
    const endX = WAVE_PADDING_LEFT + (endT / visibleEnd) * WAVE_WIDTH;

    // Draw the wave portion
    for (let i = 0; i <= steps; i++) {
        const t = startT + (i / steps) * (endT - startT);
        const x = WAVE_PADDING_LEFT + (t / visibleEnd) * WAVE_WIDTH;
        const y = getWaveY(t);
        points.push(`${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`);
    }

    // Close the path at the bottom
    const bottomY = WAVE_CENTER_Y + WAVE_AMPLITUDE + 20;
    points.push(`L ${endX.toFixed(2)} ${bottomY}`);
    points.push(`L ${startX.toFixed(2)} ${bottomY}`);
    points.push("Z");

    return points.join(" ");
}

/**
 * Calculate the position on the wave based on score and trend
 *
 * Wyckoff Cycle mapping:
 * - Accumulation (Phase 1): Low score, Bearish trend → Valley
 * - Mark-Up (Phase 2): Rising score, Bullish trend → Ascending
 * - Distribution (Phase 3): High score, Bullish trend → Peak
 * - Mark-Down (Phase 4): Falling score, Bearish trend → Descending
 */
function calculatePosition(score: number, isBullish: boolean): { x: number; y: number; phase: string } {
    let t: number;
    let phase: string;
    const visibleEnd = 0.85;

    if (isBullish) {
        // Bullish: Mark-Up or Distribution
        if (score >= 75) {
            // Distribution (peak area): score 75-100
            const progress = (score - 75) / 25;
            t = 0.40 + progress * 0.15; // t: 0.40-0.55 (around peak at 0.5)
            phase = "distribution";
        } else {
            // Mark-Up (ascending): score 0-75
            const progress = score / 75;
            t = 0.15 + progress * 0.25; // t: 0.15-0.40
            phase = "markUp";
        }
    } else {
        // Bearish: Mark-Down or Accumulation
        if (score <= 25) {
            // Accumulation (valley): score 0-25
            const progress = (25 - score) / 25;
            t = 0.0 + progress * 0.15; // t: 0.0-0.15 (valley)
            phase = "accumulation";
        } else {
            // Mark-Down (descending): score 25-100
            const progress = (100 - score) / 75;
            t = 0.55 + progress * 0.25; // t: 0.55-0.80
            phase = "markDown";
        }
    }

    const x = WAVE_PADDING_LEFT + (t / visibleEnd) * WAVE_WIDTH;
    const y = getWaveY(t);

    return { x, y, phase };
}

export function MarketCycleWave({
    totalScore,
    sp500Price,
    sp500Ma200,
    // phase is kept for API compatibility but not displayed
    phase: _phase,
    phaseNumber,
    riskLevel,
}: MarketCycleWaveProps) {
    const t = useTranslations("MarketCycle");

    const isBullish = sp500Price !== null && sp500Ma200 !== null && sp500Price > sp500Ma200;
    const position = calculatePosition(totalScore, isBullish);
    const wavePath = generateWavePath();

    const isOverbought = phaseNumber === 3 && totalScore >= 75;
    const isOversold = phaseNumber === 1 && totalScore <= 25;

    // Translate risk level
    const riskLevelMap: Record<string, string> = {
        "Low": t("risk_low"),
        "Medium": t("risk_medium"),
        "High": t("risk_high"),
    };
    const translatedRiskLevel = riskLevelMap[riskLevel] || riskLevel;

    const visibleEnd = 0.85;

    return (
        <div className="flex flex-col items-center p-4">
            {/* SVG Wave Visualization */}
            <svg
                viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
                className="w-full"
                style={{ minHeight: 220 }}
                preserveAspectRatio="xMidYMid meet"
            >
                {/* Zone filled areas - in correct Wyckoff order */}
                {/* Accumulation zone (valley/bottom - left) */}
                <path
                    d={generateZonePath(ZONES.accumulation.start, ZONES.accumulation.end)}
                    fill={PHASE_COLORS.accumulation.fill}
                    stroke={PHASE_COLORS.accumulation.stroke}
                    strokeWidth={1}
                    strokeOpacity={0.4}
                />
                {/* Mark Up zone (rising) */}
                <path
                    d={generateZonePath(ZONES.markUp.start, ZONES.markUp.end)}
                    fill={PHASE_COLORS.markUp.fill}
                    stroke={PHASE_COLORS.markUp.stroke}
                    strokeWidth={1}
                    strokeOpacity={0.4}
                />
                {/* Distribution zone (peak/top) */}
                <path
                    d={generateZonePath(ZONES.distribution.start, ZONES.distribution.end)}
                    fill={PHASE_COLORS.distribution.fill}
                    stroke={PHASE_COLORS.distribution.stroke}
                    strokeWidth={1}
                    strokeOpacity={0.4}
                />
                {/* Mark Down zone (falling) */}
                <path
                    d={generateZonePath(ZONES.markDown.start, ZONES.markDown.end)}
                    fill={PHASE_COLORS.markDown.fill}
                    stroke={PHASE_COLORS.markDown.stroke}
                    strokeWidth={1}
                    strokeOpacity={0.4}
                />

                {/* Wave path */}
                <path
                    d={wavePath}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={3}
                    className="text-gray-300 dark:text-gray-500"
                />

                {/* Zone labels at bottom - LARGER FONT */}
                <text
                    x={WAVE_PADDING_LEFT + ((ZONES.accumulation.start + ZONES.accumulation.end) / 2 / visibleEnd) * WAVE_WIDTH}
                    y={SVG_HEIGHT - 8}
                    textAnchor="middle"
                    fill={PHASE_COLORS.accumulation.text}
                    className="text-[14px] font-semibold"
                >
                    {t("phase_accumulation")}
                </text>
                <text
                    x={WAVE_PADDING_LEFT + ((ZONES.markUp.start + ZONES.markUp.end) / 2 / visibleEnd) * WAVE_WIDTH}
                    y={SVG_HEIGHT - 8}
                    textAnchor="middle"
                    fill={PHASE_COLORS.markUp.text}
                    className="text-[14px] font-semibold"
                >
                    {t("phase_markup")}
                </text>
                <text
                    x={WAVE_PADDING_LEFT + ((ZONES.distribution.start + ZONES.distribution.end) / 2 / visibleEnd) * WAVE_WIDTH}
                    y={SVG_HEIGHT - 8}
                    textAnchor="middle"
                    fill={PHASE_COLORS.distribution.text}
                    className="text-[14px] font-semibold"
                >
                    {t("phase_distribution")}
                </text>
                <text
                    x={WAVE_PADDING_LEFT + ((ZONES.markDown.start + ZONES.markDown.end) / 2 / visibleEnd) * WAVE_WIDTH}
                    y={SVG_HEIGHT - 8}
                    textAnchor="middle"
                    fill={PHASE_COLORS.markDown.text}
                    className="text-[14px] font-semibold"
                >
                    {t("phase_markdown")}
                </text>

                {/* Y-axis labels - LARGER FONT */}
                <text
                    x={12}
                    y={WAVE_CENTER_Y - WAVE_AMPLITUDE}
                    className="fill-current text-gray-400 text-[14px] font-medium"
                    dominantBaseline="middle"
                >
                    High
                </text>
                <text
                    x={12}
                    y={WAVE_CENTER_Y + WAVE_AMPLITUDE}
                    className="fill-current text-gray-400 text-[14px] font-medium"
                    dominantBaseline="middle"
                >
                    Low
                </text>

                {/* Y-axis label */}
                <text
                    x={16}
                    y={WAVE_CENTER_Y}
                    className="fill-current text-gray-500 text-[13px]"
                    transform={`rotate(-90, 16, ${WAVE_CENTER_Y})`}
                    textAnchor="middle"
                >
                    {t("market_sentiment")}
                </text>

                {/* X-axis label */}
                <text
                    x={SVG_WIDTH - 15}
                    y={SVG_HEIGHT - 21}
                    className="fill-current text-gray-500 text-[13px]"
                    textAnchor="end"
                >
                    {t("time")} →
                </text>

                {/* Indicator dot */}
                <circle
                    cx={position.x}
                    cy={position.y}
                    r={8}
                    className={
                        position.phase === "accumulation"
                            ? "fill-green-500"
                            : position.phase === "markUp"
                                ? "fill-blue-500"
                                : position.phase === "distribution"
                                    ? "fill-yellow-500"
                                    : "fill-red-500"
                    }
                    stroke="white"
                    strokeWidth={2}
                    style={{ filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.4))" }}
                />

                {/* Trend direction arrow */}
                {isBullish ? (
                    <path
                        d={`M ${position.x - 5} ${position.y - 14} L ${position.x} ${position.y - 22} L ${position.x + 5} ${position.y - 14}`}
                        fill="none"
                        stroke="#22c55e"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                ) : (
                    <path
                        d={`M ${position.x - 5} ${position.y + 14} L ${position.x} ${position.y + 22} L ${position.x + 5} ${position.y + 14}`}
                        fill="none"
                        stroke="#ef4444"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                )}

                {/* Overbought/Oversold label */}
                {isOverbought && (
                    <text
                        x={position.x}
                        y={position.y - 30}
                        textAnchor="middle"
                        className="fill-yellow-400 text-[14px] font-bold"
                    >
                        {t("overbought")}
                    </text>
                )}
                {isOversold && (
                    <text
                        x={position.x}
                        y={position.y + 35}
                        textAnchor="middle"
                        className="fill-green-400 text-[14px] font-bold"
                    >
                        {t("oversold")}
                    </text>
                )}
            </svg>

            {/* Metrics Summary - 3 blocks */}
            <div className="mt-4 flex flex-row gap-3 w-full">
                {/* Score */}
                <div className="flex-1 p-3 rounded-lg bg-muted/50 text-center flex flex-col justify-center">
                    <div className="text-xs text-muted-foreground">{t("score")}</div>
                    <div className="text-xl font-bold">{totalScore}</div>
                </div>

                {/* Risk Level */}
                <div className="flex-1 p-3 rounded-lg bg-muted/50 text-center flex flex-col justify-center">
                    <div className="text-xs text-muted-foreground">{t("risk_level")}</div>
                    <div className={`text-xl font-semibold ${RISK_COLORS[riskLevel as keyof typeof RISK_COLORS] || RISK_COLORS.Unknown}`}>
                        {translatedRiskLevel}
                    </div>
                </div>

                {/* Trend */}
                <div className="flex-1 p-3 rounded-lg bg-muted/50 text-center flex flex-col justify-center">
                    <div className="text-xs text-muted-foreground">{t("trend")}</div>
                    <div className={`text-xl font-semibold ${isBullish ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>
                        {isBullish ? t("bullish") : t("bearish")}
                    </div>
                </div>
            </div>
        </div>
    );
}
