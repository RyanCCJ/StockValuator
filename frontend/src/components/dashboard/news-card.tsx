"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { ExternalLink, Lock, Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getNewsAndResearch, type NewsItem, type ResearchItem } from "@/services/api";

interface NewsCardProps {
    symbol: string;
}

function formatRelativeTime(dateString: string | null): string {
    if (!dateString) return "";

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
        return `${diffMins}m ago`;
    } else if (diffHours < 24) {
        return `${diffHours}h ago`;
    } else if (diffDays < 7) {
        return `${diffDays}d ago`;
    } else {
        return date.toLocaleDateString();
    }
}

function NewsItemCard({ item }: { item: NewsItem }) {
    return (
        <a
            href={item.link}
            target="_blank"
            rel="noopener noreferrer"
            className="block group"
        >
            <div className="flex gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors border-b last:border-b-0">
                {item.thumbnail && (
                    <div className="flex-shrink-0 w-20 h-14 rounded overflow-hidden bg-muted">
                        <img
                            src={item.thumbnail}
                            alt=""
                            className="w-full h-full object-cover"
                        />
                    </div>
                )}
                <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium line-clamp-2 group-hover:text-primary transition-colors">
                        {item.title}
                    </h4>
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        <span>{item.publisher}</span>
                        {item.published_at && (
                            <>
                                <span>•</span>
                                <span>{formatRelativeTime(item.published_at)}</span>
                            </>
                        )}
                    </div>
                </div>
                <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
            </div>
        </a>
    );
}

function ResearchItemCard({ item }: { item: ResearchItem }) {
    return (
        <a
            href={item.link}
            target="_blank"
            rel="noopener noreferrer"
            className="block group"
        >
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors border-b last:border-b-0">
                <Lock className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium line-clamp-2 group-hover:text-primary transition-colors">
                        {item.title}
                    </h4>
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        <span>{item.publisher}</span>
                        {item.published_at && (
                            <>
                                <span>•</span>
                                <span>{formatRelativeTime(item.published_at)}</span>
                            </>
                        )}
                    </div>
                </div>
                <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
            </div>
        </a>
    );
}

export function NewsCard({ symbol }: NewsCardProps) {
    const t = useTranslations("NewsResearch");

    const { data, isLoading, error } = useQuery({
        queryKey: ["newsResearch", symbol],
        queryFn: () => getNewsAndResearch(symbol),
        staleTime: 3600000, // 1 hour
    });

    if (isLoading) {
        return (
            <Card>
                <CardContent className="flex items-center justify-center min-h-[200px]">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </CardContent>
            </Card>
        );
    }

    if (error || !data) {
        return null; // Silently fail - news is supplementary
    }

    const hasNews = data.news && data.news.length > 0;
    const hasResearch = data.research && data.research.length > 0;

    if (!hasNews && !hasResearch) {
        return null; // No content to show
    }

    return (
        <Card>
            <CardHeader className="pb-3">
                <CardTitle className="text-lg">
                    {t("title")}
                </CardTitle>
            </CardHeader>
            <CardContent>
                {hasNews && hasResearch ? (
                    <Tabs defaultValue="news" className="w-full">
                        <TabsList className="w-full mb-3">
                            <TabsTrigger value="news" className="flex-1">
                                {t("news")} ({data.news.length})
                            </TabsTrigger>
                            <TabsTrigger value="research" className="flex-1">
                                {t("research")} ({data.research.length})
                            </TabsTrigger>
                        </TabsList>
                        <TabsContent value="news" className="mt-0">
                            <div className="max-h-[400px] overflow-y-auto">
                                {data.news.map((item, idx) => (
                                    <NewsItemCard key={idx} item={item} />
                                ))}
                            </div>
                        </TabsContent>
                        <TabsContent value="research" className="mt-0">
                            <div className="max-h-[400px] overflow-y-auto">
                                {data.research.map((item, idx) => (
                                    <ResearchItemCard key={idx} item={item} />
                                ))}
                            </div>
                        </TabsContent>
                    </Tabs>
                ) : hasNews ? (
                    <div className="max-h-[400px] overflow-y-auto">
                        {data.news.map((item, idx) => (
                            <NewsItemCard key={idx} item={item} />
                        ))}
                    </div>
                ) : (
                    <div className="max-h-[400px] overflow-y-auto">
                        {data.research.map((item, idx) => (
                            <ResearchItemCard key={idx} item={item} />
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
