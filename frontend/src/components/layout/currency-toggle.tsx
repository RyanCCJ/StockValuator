"use client";

import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DollarSign } from "lucide-react";
import { useCurrency } from "@/context/currency-context";

export function CurrencyToggle() {
    const t = useTranslations("Sidebar");
    const tCurrency = useTranslations("Currency");
    const { currency, setCurrency, isLoading } = useCurrency();

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="w-full justify-start text-muted-foreground">
                    <DollarSign className="h-4 w-4 mr-2" />
                    <span>{t('currency')}</span>
                    <span className="ml-auto text-xs opacity-50 uppercase">
                        {isLoading ? "..." : tCurrency(currency.toLowerCase())}
                    </span>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setCurrency("USD")}>{tCurrency('usd')}</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setCurrency("TWD")}>{tCurrency('twd')}</DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
