import { Scale } from "lucide-react";

export const Header = () => {
  return (
    <header className="relative overflow-hidden" style={{ background: "var(--gradient-header)" }}>
      <div className="absolute inset-0 opacity-10 [background-image:radial-gradient(circle_at_1px_1px,white_1px,transparent_0)] [background-size:24px_24px]" />
      <div className="container relative mx-auto px-6 py-10 md:py-14">
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
      </div>
    </header>
  );
};
