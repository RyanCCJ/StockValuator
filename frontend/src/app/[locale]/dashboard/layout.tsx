"use client";

import { useSession } from "next-auth/react";
import { redirect, usePathname } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Sidebar } from "@/components/layout/sidebar";

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
        <div className="flex min-h-screen">
            <Sidebar accessToken={accessToken} />
            <main className="flex-1 p-6 overflow-auto">
                {children}
            </main>
        </div>
    );
}
