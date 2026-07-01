"use client";

import { parseAsString, useQueryStates } from "nuqs";
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { Input } from "@/components/ui/input";
import type { RegistrationStatsData } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const chartConfig = {
  count: {
    label: "Registrations",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

const granularityParsers = {
  granularity: parseAsString.withDefault("month"),
  from: parseAsString.withDefault(""),
  to: parseAsString.withDefault(""),
};

type AdminRegistrationChartProps = {
  stats: RegistrationStatsData;
  title: string;
  description: string;
};

export function AdminRegistrationChart({
  stats,
  title,
  description,
}: AdminRegistrationChartProps) {
  const [filters, setFilters] = useQueryStates(granularityParsers);
  const growthPositive = stats.growth_percent >= 0;

  return (
    <Card>
      <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
        <div className="flex flex-col items-start gap-2 sm:items-end">
          <Badge
            variant="outline"
            className={cn(
              growthPositive
                ? "border-green-500/30 text-green-700 dark:text-green-400"
                : "border-red-500/30 text-red-700 dark:text-red-400",
            )}
          >
            {growthPositive ? "+" : ""}
            {stats.growth_percent.toFixed(1)}% {stats.growth_label}
          </Badge>
          <p className="text-xs text-muted-foreground">
            {stats.total_in_range} in selected range
          </p>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {(["month", "week", "custom"] as const).map((value) => (
            <Button
              key={value}
              type="button"
              size="sm"
              variant={filters.granularity === value ? "default" : "outline"}
              onClick={() => {
                void setFilters({ granularity: value });
              }}
            >
              {value === "month"
                ? "Monthly"
                : value === "week"
                  ? "Weekly"
                  : "Custom"}
            </Button>
          ))}
        </div>

        {filters.granularity === "custom" ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label htmlFor="stats-from" className="text-xs font-medium text-muted-foreground">
                From
              </label>
              <Input
                id="stats-from"
                type="date"
                value={filters.from}
                onChange={(event) => {
                  void setFilters({ from: event.target.value });
                }}
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="stats-to" className="text-xs font-medium text-muted-foreground">
                To
              </label>
              <Input
                id="stats-to"
                type="date"
                value={filters.to}
                onChange={(event) => {
                  void setFilters({ to: event.target.value });
                }}
              />
            </div>
          </div>
        ) : null}

        {stats.series.length === 0 ? (
          <p className="rounded-lg border border-dashed px-4 py-8 text-center text-sm text-muted-foreground">
            No registration data in this period.
          </p>
        ) : (
          <ChartContainer config={chartConfig} className="aspect-[2/1] w-full">
            <LineChart data={stats.series} margin={{ left: 8, right: 8, top: 8 }}>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="label"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                minTickGap={24}
              />
              <YAxis tickLine={false} axisLine={false} width={32} allowDecimals={false} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Line
                type="monotone"
                dataKey="count"
                stroke="var(--color-count)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
