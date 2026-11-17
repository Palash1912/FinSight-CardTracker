import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CreditCard, FileUp, Gift } from "lucide-react";

interface QuickAction {
  title: string;
  description: string;
  icon: React.ElementType;
  iconColor: string;
  href: string;
}

const actions: QuickAction[] = [
  {
    title: "Add a Card",
    description: "Register a new credit card to start tracking spend and rewards.",
    icon: CreditCard,
    iconColor: "text-blue-600 bg-blue-100",
    href: "/cards",
  },
  {
    title: "Upload Statement",
    description: "Upload a bank statement PDF to automatically import transactions.",
    icon: FileUp,
    iconColor: "text-emerald-600 bg-emerald-100",
    href: "/statements/upload",
  },
  {
    title: "Check Rewards",
    description: "View your earned rewards and discover optimization tips.",
    icon: Gift,
    iconColor: "text-purple-600 bg-purple-100",
    href: "/rewards",
  },
];

export function QuickActions() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {actions.map((action) => (
        <Card
          key={action.title}
          className="group transition-all hover:shadow-md hover:border-primary/20"
        >
          <CardContent className="flex flex-col items-start gap-4 p-6">
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-xl ${action.iconColor} transition-transform group-hover:scale-110`}
            >
              <action.icon className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <h3 className="font-semibold text-foreground">{action.title}</h3>
              <p className="text-sm text-muted-foreground">
                {action.description}
              </p>
            </div>
            <Button variant="outline" size="sm" className="mt-auto" asChild>
              <Link href={action.href}>Get Started</Link>
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
