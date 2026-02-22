"use client";

import { useSession, signOut } from "next-auth/react";
import { redirect, usePathname } from "next/navigation";
import { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { Sidebar } from "@/components/layout/sidebar";
import { ErrorBoundary } from "@/components/layout/error-boundary";
import { AUTH_ERROR_EVENT } from "@/services/api";

interface DashboardLayoutProps {
    children: React.ReactNode;
    params: Promise<{ locale: string }>;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
    const { data: session, status } = useSession();
    const pathname = usePathname();

    // Extract locale from pathname
    const locale = pathname.split('/')[1];
    const accessToken = (session as { accessToken?: string })?.accessToken;

    // Listen for 401 errors and auto-logout
    useEffect(() => {
        const handleAuthError = () => {
            signOut({ callbackUrl: `/${locale}/login` });
        };

        window.addEventListener(AUTH_ERROR_EVENT, handleAuthError);
        return () => {
            window.removeEventListener(AUTH_ERROR_EVENT, handleAuthError);
        };
    }, [locale]);

    if (status === "loading") {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin" />
            </div>
        );
    }

    if (!session) {
        redirect(`/${locale}/login`);
    }

    return (
        <div className="flex min-h-screen flex-col md:flex-row">
            <Sidebar accessToken={accessToken} />
            <main className="flex-1 p-6 overflow-auto">
                <ErrorBoundary>
                    {children}
                </ErrorBoundary>
            </main>
        </div>
    );
}
