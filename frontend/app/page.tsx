'use client';

import Layout from "@/components/Layout";
import Dashboard from "@/components/Dashboard";
import { Analysis } from "@/components/Analysis";
import { Portfolio } from "@/components/Portfolio"; // Import the real component
import { useTickerStore } from "@/store/tickerStore";

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