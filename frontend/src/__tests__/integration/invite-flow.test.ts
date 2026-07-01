jest.mock("@/env", () => ({
  env: {
    FASTAPI_URL: "http://localhost:8000",
    NODE_ENV: "test",
  },
}));

const mockedValidate = jest.fn();
const mockedAccept = jest.fn();

jest.mock("@/lib/api/org", () => ({
  validateInviteWithFastApi: (...args: unknown[]) => mockedValidate(...args),
  acceptInviteWithFastApi: (...args: unknown[]) => mockedAccept(...args),
  validateInvite: (...args: unknown[]) => mockedValidate(...args),
  acceptInvite: (...args: unknown[]) => mockedAccept(...args),
}));

jest.mock("next/navigation", () => ({
  redirect: jest.fn(),
}));

import { acceptInviteAction } from "@/actions/invite";
import { validateInvite } from "@/lib/api/org";
import { redirect } from "next/navigation";

const mockedRedirect = redirect as jest.MockedFunction<typeof redirect>;

describe("invite flow", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("validateInvite delegates to FastAPI client", async () => {
    mockedValidate.mockResolvedValue({
      response: { status: 200 },
      body: {
        success: true,
        data: { valid: true, org_name: "Acme", role: "employee" },
      },
    });

    const result = await validateInvite("token-abc");
    expect(mockedValidate).toHaveBeenCalledWith("token-abc");
    expect(result.body.data.valid).toBe(true);
  });

  it("acceptInviteAction calls acceptInvite and redirects on success", async () => {
    mockedAccept.mockResolvedValue({
      response: { status: 201, headers: new Headers() },
      body: {
        success: true,
        data: {
          user_id: "u1",
          email: "new@example.com",
          role: "employee",
          org_id: "org-1",
        },
      },
    });

    const formData = new FormData();
    formData.set("token", "token-abc");
    formData.set("email", "new@example.com");
    formData.set("password", "password123");
    formData.set("full_name", "New Hire");

    await acceptInviteAction({}, formData);

    expect(mockedAccept).toHaveBeenCalledWith({
      token: "token-abc",
      email: "new@example.com",
      password: "password123",
      full_name: "New Hire",
    });
    expect(mockedRedirect).toHaveBeenCalledWith("/dashboard");
  });
});
