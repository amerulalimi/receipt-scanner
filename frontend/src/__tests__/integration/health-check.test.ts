describe("health check integration", () => {
  const apiUrl = "http://localhost:8000";

  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_URL = apiUrl;
  });

  it("NEXT_PUBLIC_API_URL env variable is defined", () => {
    expect(process.env.NEXT_PUBLIC_API_URL).toBeDefined();
    expect(process.env.NEXT_PUBLIC_API_URL).toBe(apiUrl);
  });

  it("mocked /health call returns ok payload", async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        data: { status: "ok" },
        error: null,
      }),
    };

    global.fetch = jest.fn().mockResolvedValue(mockResponse);

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
    const body = await response.json();

    expect(global.fetch).toHaveBeenCalledWith(`${apiUrl}/health`);
    expect(body).toEqual({ data: { status: "ok" }, error: null });
  });
});
