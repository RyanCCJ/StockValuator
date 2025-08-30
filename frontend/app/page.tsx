'use client';

import Layout from "@/components/Layout";
import Dashboard from "@/components/Dashboard";
import { Analysis } from "@/components/Analysis";
import { useTickerStore } from "@/store/tickerStore";

// A simple component for the placeholder portfolio page
const Portfolio = () => (
  <div className="flex items-center justify-center h-96 border-2 border-dashed rounded-lg">
    <p className="text-muted-foreground">Portfolio Page - Coming Soon</p>
  </div>
);

const PageContent = () => {
  const { activePage } = useTickerStore();

  switch (activePage) {
    case 'dashboard':
      return <Dashboard />;
    case 'analysis':
      return <Analysis />;
    case 'portfolio':
      return <Portfolio />;
    default:
      return <Dashboard />;
  }
};

export default function Home() {
  return (
    <Layout>
      <div className="px-4 md:px-8 py-6">
        <PageContent />
      </div>
    </Layout>
  );
}
