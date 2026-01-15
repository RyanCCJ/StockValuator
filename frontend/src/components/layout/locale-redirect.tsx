"use client";

import { useEffect } from "react";
import { useLocale } from "next-intl";
import { usePathname, useRouter } from "@/i18n/routing";

const LOCALE_STORAGE_KEY = "preferred-locale";
const VALID_LOCALES = ["en", "zh-TW"];

/**
 * Component that reads the preferred locale from localStorage
 * and redirects if it differs from the current URL locale.
 * Should be placed in the root layout.
 */
export function LocaleRedirect() {
    const currentLocale = useLocale();
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        const savedLocale = localStorage.getItem(LOCALE_STORAGE_KEY);

        // Only redirect if saved locale is valid and different from current
        if (
            savedLocale &&
            VALID_LOCALES.includes(savedLocale) &&
            savedLocale !== currentLocale
        ) {
            router.replace(pathname, { locale: savedLocale });
        }
    }, [currentLocale, pathname, router]);

    return null;
}
