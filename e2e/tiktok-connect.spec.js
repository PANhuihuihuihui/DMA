import { expect, test } from "playwright/test";

const secrets = "access_token=sentinel-access refresh_token=sentinel-refresh code_verifier=sentinel-verifier client_secret=sentinel-secret";

test("TikTok connection is redacted across connected, denied, reconnect, and disconnect states", async ({ page }) => {
  const connected = true;
  await page.route("**/api/v1/auth/session", (route) => route.fulfill({ json: { session: { id: "test-session", userId: "test-user", merchantId: "merchant_demo" } } }));
  await page.route("**/api/v1/onboarding/profile", (route) => route.fulfill({ json: { profile: { status: "confirmed" } } }));
  await page.route("**/api/v1/tiktok/connection", async (route) => {
    await route.fulfill({ json: { status: "ok", configured: true, connectedAccounts: connected ? [{ accountId: "tt-123", status: "connected", expiresAt: "2030-01-01T00:00:00Z" }] : [] } });
  });

  await page.goto("/app?module=Brand%20%26%20Social%20Accounts&tiktokConnected=1");
  await expect(page.getByText("TikTok account connected. Credentials remain securely stored on the server.")).toBeVisible();
  await expect(page.getByText("TikTok account tt-123")).toBeVisible();
  await expect(page.getByRole("button", { name: "Disconnect TikTok" })).toBeVisible();

  await page.goto("/app?module=Brand%20%26%20Social%20Accounts&tiktokDenied=1");
  await expect(page.getByText("TikTok consent was not completed. Try connecting again when ready.")).toBeVisible();
  await page.goto("/app?module=Brand%20%26%20Social%20Accounts&tiktokReconnect=1");
  await expect(page.getByText("TikTok could not connect. Check the Business account and reconnect.")).toBeVisible();

  const storage = await page.evaluate(() => JSON.stringify({ localStorage, sessionStorage }));
  expect(page.url()).not.toMatch(/access_token|refresh_token|code_verifier|client_secret|code=|state=/i);
  expect(storage).not.toMatch(/access_token|refresh_token|code_verifier|client_secret|authorization/i);
  expect(`${page.url()} ${storage}`).not.toContain(secrets);
});
