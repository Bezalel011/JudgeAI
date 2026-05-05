import { Bell, Scale } from "lucide-react";

interface Props {
  unreadAlerts?: number;
}

export const Header = ({ unreadAlerts = 0 }: Props) => {
  return (
    <header className="relative overflow-hidden" style={{ background: "var(--gradient-header)" }}>
      <div className="absolute inset-0 opacity-10 [background-image:radial-gradient(circle_at_1px_1px,white_1px,transparent_0)] [background-size:24px_24px]" />
      <div className="container relative mx-auto px-6 py-10 md:py-14">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-foreground/10 ring-1 ring-primary-foreground/20 backdrop-blur">
            <Scale className="h-7 w-7 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-primary-foreground md:text-3xl">
              Court Judgment Analyzer
            </h1>
            <p className="mt-1 text-sm text-primary-foreground/80 md:text-base">
              From Legal Text to Verified Action Plans
            </p>
          </div>
          </div>
          <div className="flex items-center gap-3 rounded-full border border-primary-foreground/20 bg-primary-foreground/10 px-4 py-2 text-primary-foreground backdrop-blur">
            <Bell className="h-4 w-4" />
            <span className="text-sm font-medium">Alerts</span>
            <span className="inline-flex min-w-7 items-center justify-center rounded-full bg-primary-foreground px-2 py-0.5 text-xs font-bold text-primary">
              {unreadAlerts}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
