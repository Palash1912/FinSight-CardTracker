import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { OverviewCards } from "@/components/dashboard/overview-cards";
import { SpendCharts } from "@/components/dashboard/spend-charts";
import { RecentTransactions } from "@/components/dashboard/recent-transactions";
import { QuickActions } from "@/components/dashboard/quick-actions";

export default function DashboardPage() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl space-y-8">
            {/* Overview Metrics */}
            <section>
              <h2 className="mb-4 text-lg font-semibold text-foreground">
                Overview
              </h2>
              <OverviewCards />
            </section>

            {/* Spend Analytics Charts */}
            <section>
              <SpendCharts />
            </section>

            {/* Quick Actions */}
            <section>
              <h2 className="mb-4 text-lg font-semibold text-foreground">
                Quick Actions
              </h2>
              <QuickActions />
            </section>

            {/* Recent Transactions */}
            <section>
              <h2 className="mb-4 text-lg font-semibold text-foreground">
                Recent Transactions
              </h2>
              <RecentTransactions />
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
