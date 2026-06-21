import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { OrgAnalyticsData } from "@/lib/api/types";
import { getCategoryLabel } from "@/lib/constants/receipts";

type OrgAnalyticsSectionProps = {
  analytics: OrgAnalyticsData;
  categoryLabels: Record<string, string>;
};

function formatRinggit(value: number | string): string {
  return new Intl.NumberFormat("en-MY", {
    style: "currency",
    currency: "MYR",
    minimumFractionDigits: 2,
  }).format(Number(value));
}

function formatMonth(value: string | null): string {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("en-MY", {
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function OrgAnalyticsSection({
  analytics,
  categoryLabels,
}: OrgAnalyticsSectionProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Approval turnaround</CardTitle>
          <CardDescription>
            Tax year {analytics.tax_year} — reviewed receipts
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-sm text-muted-foreground">Average hours</p>
            <p className="text-2xl font-semibold tabular-nums">
              {analytics.turnaround.average_hours.toFixed(1)}h
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Receipts reviewed</p>
            <p className="text-2xl font-semibold tabular-nums">
              {analytics.turnaround.reviewed_count}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Spend by category</CardTitle>
          <CardDescription>Monthly claim totals by relief category</CardDescription>
        </CardHeader>
        <CardContent>
          {analytics.category_trend.length === 0 ? (
            <p className="text-sm text-muted-foreground">No claim data yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">Month</th>
                    <th className="pb-2 pr-4 font-medium">Category</th>
                    <th className="pb-2 font-medium text-right">Claimed</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.category_trend.map((row, index) => (
                    <tr key={`${row.category}-${row.month}-${index}`} className="border-b last:border-0">
                      <td className="py-2 pr-4">{formatMonth(row.month)}</td>
                      <td className="py-2 pr-4">
                        {getCategoryLabel(row.category, categoryLabels)}
                      </td>
                      <td className="py-2 text-right tabular-nums">
                        {formatRinggit(row.total_claimed)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top claiming employees</CardTitle>
          <CardDescription>Approved claims by employee</CardDescription>
        </CardHeader>
        <CardContent>
          {analytics.top_employees.length === 0 ? (
            <p className="text-sm text-muted-foreground">No employee claims yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4 font-medium">Employee</th>
                    <th className="pb-2 pr-4 font-medium">Receipts</th>
                    <th className="pb-2 font-medium text-right">Total claimed</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.top_employees.map((employee) => (
                    <tr key={employee.user_id} className="border-b last:border-0">
                      <td className="py-2 pr-4">
                        <p className="font-medium">
                          {employee.full_name ?? employee.email}
                        </p>
                        <p className="text-xs text-muted-foreground">{employee.email}</p>
                      </td>
                      <td className="py-2 pr-4 tabular-nums">{employee.receipt_count}</td>
                      <td className="py-2 text-right tabular-nums">
                        {formatRinggit(employee.total_claimed)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Rejection reasons</CardTitle>
            <CardDescription>Why claims were rejected</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.rejections.length === 0 ? (
              <p className="text-sm text-muted-foreground">No rejections recorded.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {analytics.rejections.map((item) => (
                  <li
                    key={item.reason}
                    className="flex items-center justify-between gap-2 rounded-md border px-3 py-2"
                  >
                    <span>{item.reason}</span>
                    <span className="font-medium tabular-nums">{item.count}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Year-end forecast</CardTitle>
            <CardDescription>Projected relief utilization</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.forecast.length === 0 ? (
              <p className="text-sm text-muted-foreground">No forecast data yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-muted-foreground">
                      <th className="pb-2 pr-4 font-medium">Category</th>
                      <th className="pb-2 pr-4 font-medium text-right">YTD</th>
                      <th className="pb-2 pr-4 font-medium text-right">Projected</th>
                      <th className="pb-2 font-medium text-right">Utilization</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.forecast.map((row) => (
                      <tr key={row.category} className="border-b last:border-0">
                        <td className="py-2 pr-4">
                          {getCategoryLabel(row.category, categoryLabels)}
                        </td>
                        <td className="py-2 pr-4 text-right tabular-nums">
                          {formatRinggit(row.approved_to_date)}
                        </td>
                        <td className="py-2 pr-4 text-right tabular-nums">
                          {formatRinggit(row.projected_year_end)}
                        </td>
                        <td className="py-2 text-right tabular-nums">
                          {row.utilization_pct.toFixed(0)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
