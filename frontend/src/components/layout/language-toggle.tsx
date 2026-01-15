"use client";

import { useLocale, useTranslations } from "next-intl";
import { usePathname, useRouter } from "@/i18n/routing";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Globe } from "lucide-react";

const LOCALE_STORAGE_KEY = "preferred-locale";

export function LanguageToggle() {
    const t = useTranslations("Sidebar");
    const locale = useLocale();
    const router = useRouter();
    const pathname = usePathname();

    const switchLocale = (newLocale: string) => {
        // Save to localStorage
        if (typeof window !== "undefined") {
            localStorage.setItem(LOCALE_STORAGE_KEY, newLocale);
        }
        router.replace(pathname, { locale: newLocale });
    };

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="w-full justify-start text-muted-foreground">
                    <Globe className="h-4 w-4 mr-2" />
                    <span>{t('language')}</span>
                    <span className="ml-auto text-xs opacity-50 uppercase">
                        {locale === 'zh-TW' ? '繁中' : 'EN'}
                    </span>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => switchLocale("en")}>English</DropdownMenuItem>
                <DropdownMenuItem onClick={() => switchLocale("zh-TW")}>繁體中文</DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
