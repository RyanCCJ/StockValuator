"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Settings } from "lucide-react";
import { createCategory, deleteCategory, Category } from "@/services/api";
import { useTranslations } from "next-intl";

interface CategoryManagerProps {
    accessToken: string | undefined;
    categories: Category[];
    onUpdate: () => void;
}

export function CategoryManager({ accessToken, categories, onUpdate }: CategoryManagerProps) {
    const t = useTranslations("Watchlist");
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [newCategoryName, setNewCategoryName] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!accessToken || !newCategoryName.trim()) return;

        setIsLoading(true);
        try {
            await createCategory(accessToken, newCategoryName.trim());
            setNewCategoryName("");
            setIsCreateOpen(false);
            onUpdate();
        } catch (error) {
            console.error("Failed to create category:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (categoryId: string) => {
        if (!accessToken) return;
        try {
            await deleteCategory(accessToken, categoryId);
            onUpdate();
        } catch (error) {
            console.error("Failed to delete category:", error);
        }
    };

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-7 px-2">
                    <Settings className="h-4 w-4" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
                <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                    <DialogTrigger asChild>
                        <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                            {t('new_category')}
                        </DropdownMenuItem>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[350px]">
                        <DialogHeader>
                            <DialogTitle>{t('create_category_title')}</DialogTitle>
                            <DialogDescription>
                                {t('create_category_desc')}
                            </DialogDescription>
                        </DialogHeader>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">{t('category_name')}</Label>
                                <Input
                                    id="name"
                                    placeholder={t('category_placeholder')}
                                    value={newCategoryName}
                                    onChange={(e) => setNewCategoryName(e.target.value)}
                                    disabled={isLoading}
                                />
                            </div>
                            <div className="flex gap-2 justify-end">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => setIsCreateOpen(false)}
                                    disabled={isLoading}
                                >
                                    {t('cancel')}
                                </Button>
                                <Button type="submit" disabled={isLoading || !newCategoryName.trim()}>
                                    {isLoading ? t('creating') : t('create')}
                                </Button>
                            </div>
                        </form>
                    </DialogContent>
                </Dialog>

                {categories.length > 0 && (
                    <>
                        <div className="h-px bg-border my-1" />
                        <div className="px-2 py-1 text-xs text-muted-foreground">{t('delete_category')}</div>
                        {categories.map((cat) => (
                            <DropdownMenuItem
                                key={cat.id}
                                className="text-destructive focus:text-destructive"
                                onSelect={() => handleDelete(cat.id)}
                            >
                                × {cat.name}
                            </DropdownMenuItem>
                        ))}
                    </>
                )}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
