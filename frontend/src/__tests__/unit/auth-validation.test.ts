import {
  loginSchema,
  registerSchema,
  updateProfileSchema,
} from "@/lib/validations/auth";

describe("loginSchema", () => {
  it("rejects empty email", () => {
    const result = loginSchema.safeParse({ email: "", password: "secret" });
    expect(result.success).toBe(false);
  });

  it("rejects invalid email format", () => {
    const result = loginSchema.safeParse({
      email: "not-an-email",
      password: "secret",
    });
    expect(result.success).toBe(false);
  });
});

describe("registerSchema", () => {
  it("rejects password under 8 chars", () => {
    const result = registerSchema.safeParse({
      email: "user@example.com",
      password: "short",
      full_name: "Ahmad",
      account_type: "individual",
    });
    expect(result.success).toBe(false);
  });

  it("accepts valid data", () => {
    const result = registerSchema.safeParse({
      email: "user@example.com",
      password: "password123",
      full_name: "Ahmad",
      account_type: "corporate",
    });
    expect(result.success).toBe(true);
  });
});

describe("updateProfileSchema", () => {
  it("allows partial updates", () => {
    const result = updateProfileSchema.safeParse({
      tax_year: 2025,
    });
    expect(result.success).toBe(true);
  });
});
