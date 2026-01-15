"use client";

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { getStockPrice } from "@/services/api";

type CurrencyCode = "USD" | "TWD";

interface CurrencyContextType {
    currency: CurrencyCode;
    exchangeRate: number;
    isLoading: boolean;
    setCurrency: (currency: CurrencyCode) => void;
    formatMoney: (amountInUSD: number) => string;
}

const CurrencyContext = createContext<CurrencyContextType | undefined>(undefined);

const STORAGE_KEY = "preferred-currency";

export function CurrencyProvider({ children }: { children: ReactNode }) {
    const [currency, setCurrencyState] = useState<CurrencyCode>("USD");
    const [exchangeRate, setExchangeRate] = useState<number>(1);
    const [isLoading, setIsLoading] = useState(false);

    // Load saved preference
    useEffect(() => {
        const saved = localStorage.getItem(STORAGE_KEY) as CurrencyCode | null;
        if (saved === "TWD" || saved === "USD") {
            setCurrencyState(saved);
        }
    }, []);

    // Fetch exchange rate when currency changes to TWD
    const fetchExchangeRate = useCallback(async () => {
        if (currency === "USD") {
            setExchangeRate(1);
            return;
        }

        setIsLoading(true);
        try {
            const data = await getStockPrice("TWD=X");
            if (data?.price) {
                setExchangeRate(data.price);
            }
        } catch (error) {
            console.error("Failed to fetch exchange rate:", error);
            // Fallback to a reasonable default if API fails
            setExchangeRate(32);
        } finally {
            setIsLoading(false);
        }
    }, [currency]);

    useEffect(() => {
        fetchExchangeRate();
    }, [fetchExchangeRate]);

    const setCurrency = useCallback((newCurrency: CurrencyCode) => {
        setCurrencyState(newCurrency);
        localStorage.setItem(STORAGE_KEY, newCurrency);
    }, []);

    const formatMoney = useCallback(
        (amountInUSD: number) => {
            const convertedAmount = amountInUSD * exchangeRate;
            const currencySymbol = currency === "USD" ? "$" : "NT$";
            const locale = currency === "USD" ? "en-US" : "zh-TW";

            return new Intl.NumberFormat(locale, {
                style: "decimal",
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            }).format(convertedAmount).replace(/^/, currencySymbol);
        },
        [currency, exchangeRate]
    );

    return (
        <CurrencyContext.Provider
            value={{
                currency,
                exchangeRate,
                isLoading,
                setCurrency,
                formatMoney,
            }}
        >
            {children}
        </CurrencyContext.Provider>
    );
}

export function useCurrency() {
    const context = useContext(CurrencyContext);
    if (context === undefined) {
        throw new Error("useCurrency must be used within a CurrencyProvider");
    }
    return context;
}
