"use client";

import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useTranslations } from "next-intl";

interface PaginationControlsProps {
    currentPage: number;
    pageSize: number;
    totalCount: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (size: number) => void;
}

export function PaginationControls({
    currentPage,
    pageSize,
    totalCount,
    onPageChange,
    onPageSizeChange,
}: PaginationControlsProps) {
    const t = useTranslations("Common");
    const totalPages = Math.ceil(totalCount / pageSize);

    if (totalCount === 0) return null;

    return (
        <div className="flex items-center justify-between px-2 py-4 border-t">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>
                    {t("showing")} {(currentPage - 1) * pageSize + 1} {t("to")}{" "}
                    {Math.min(currentPage * pageSize, totalCount)} {t("of")} {totalCount}
                </span>
            </div>
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">{t("rows_per_page")}</span>
                    <select
                        className="h-8 w-16 rounded-md border border-input bg-transparent px-2 text-sm"
                        value={pageSize}
                        onChange={(e) => {
                            onPageSizeChange(Number(e.target.value));
                            onPageChange(1);
                        }}
                    >
                        <option value={10}>10</option>
                        <option value={25}>25</option>
                        <option value={50}>50</option>
                        <option value={100}>100</option>
                    </select>
                </div>
                <div className="flex items-center gap-1">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onPageChange(Math.max(1, currentPage - 1))}
                        disabled={currentPage === 1}
                    >
                        <ChevronLeft className="h-4 w-4" />
                        {t("previous")}
                    </Button>
                    <span className="px-2 text-sm">
                        {t("page")} {currentPage} {t("of")} {totalPages}
                    </span>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
                        disabled={currentPage >= totalPages}
                    >
                        {t("next")}
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    );
}
