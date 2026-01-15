"use client";

import { SessionProvider } from "next-auth/react";
import { ThemeProvider } from "next-themes";
import { CurrencyProvider } from "@/context/currency-context";
import { LocaleRedirect } from "@/components/layout/locale-redirect";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <SessionProvider>
            <ThemeProvider
                attribute="class"
                defaultTheme="dark"
                enableSystem
                disableTransitionOnChange
            >
                <CurrencyProvider>
                    <LocaleRedirect />
                    {children}
                </CurrencyProvider>
            </ThemeProvider>
        </SessionProvider>
    );
}
