import { expect, test } from "playwright/test";

test("Instagram connection renders safe status and has no credential in browser state", async ({ page }) => {
  let connectionRequested = false;
  await page.route("**/api/v1/auth/session", async (route) => {
    await route.fulfill({ json: { session: { id: "test-session", userId: "test-user", merchantId: "merchant_demo" } } });
  });
  await page.route("**/api/v1/instagram/connection", async (route) => {
    if (route.request().method() === "GET") {
      connectionRequested = true;
      await route.fulfill({ json: { status: "ok", configured: true, connectedAccounts: [{ accountId: "ig-123", status: "connected", expiresAt: "2030-01-01T00:00:00Z" }] } });
      return;
    }
    await route.fulfill({ json: { status: "ok", connectedAccounts: [] } });
  });
  await page.goto("/app?module=Brand%20%26%20Social%20Accounts&instagramConnected=1");
  await expect.poll(() => connectionRequested).toBe(true);
  await expect(page.getByText("Instagram account connected. Credentials remain securely stored on the server.")).toBeVisible();
  const url = page.url();
  const storage = await page.evaluate(() => JSON.stringify({ localStorage, sessionStorage }));
  expect(url).not.toMatch(/access_token|code=|state=/i);
  expect(storage).not.toMatch(/access_token|refresh_token|authorization/i);
});
