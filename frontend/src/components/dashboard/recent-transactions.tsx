import { Card, CardContent } from "@/components/ui/card";
import { ReceiptText } from "lucide-react";

export function RecentTransactions() {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-16">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
          <ReceiptText className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="mt-4 text-lg font-semibold text-foreground">
          No transactions yet
        </h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload a bank statement to see your transactions here
        </p>
      </CardContent>
    </Card>
  );
}
