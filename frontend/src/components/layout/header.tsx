import { Bell, User } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  title?: string;
}

export function Header({ title = "Dashboard" }: HeaderProps) {
  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b bg-card px-4 md:px-6">
      {/* Page title — offset on mobile to make room for hamburger */}
      <h1 className="pl-12 text-xl font-semibold text-foreground md:pl-0">
        {title}
      </h1>

      {/* Right side actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5 text-muted-foreground" />
          {/* Notification dot placeholder */}
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-destructive" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="rounded-full"
          aria-label="User menu"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
            <User className="h-4 w-4" />
          </div>
        </Button>
      </div>
    </header>
  );
}
