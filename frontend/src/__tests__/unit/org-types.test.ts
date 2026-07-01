import type { OrgEmployeeItem } from "@/lib/api/types";
import {
  computeEmployeeStatus,
  formatPayrollFilename,
} from "@/lib/types/org";

describe("org types helpers", () => {
  const employee: OrgEmployeeItem = {
    user_id: "user-1",
    full_name: "Ali",
    email: "ali@example.com",
    role: "employee",
    is_active: true,
    receipts_count: 2,
    total_claimed: 100,
    pending_count: 0,
  };

  it("computeEmployeeStatus returns active/inactive", () => {
    expect(computeEmployeeStatus(employee)).toBe("active");
    expect(
      computeEmployeeStatus({ ...employee, is_active: false }),
    ).toBe("inactive");
  });

  it("formatPayrollFilename sanitizes org name", () => {
    expect(formatPayrollFilename("Acme Sdn Bhd", 2025)).toBe(
      "SyarikatAcmeSdnBhd_BE_2025_payroll.csv",
    );
  });
});
