import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawn } from "node:child_process";
import { chromium } from "playwright";

const tempDir = await mkdtemp(join(tmpdir(), "localpilot-phase3-screens-"));
const dbPath = join(tempDir, "phase3.sqlite");
const apiPort = Number(process.env.PHASE3_SCREEN_API_PORT || 8798);
const webPort = Number(process.env.PHASE3_SCREEN_WEB_PORT || 5193);
const apiUrl = `http://127.0.0.1:${apiPort}`;
const webUrl = `http://127.0.0.1:${webPort}`;
const children = [];

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const start = (name, command, args, options = {}) => {
  const child = spawn(command, args, {
    stdio: ["ignore", "pipe", "pipe"],
    env: {
      ...process.env,
      ...(options.env || {}),
    },
  });
  child.stdoutText = "";
  child.stderrText = "";
  child.stdout.on("data", (chunk) => {
    child.stdoutText += chunk.toString();
  });
  child.stderr.on("data", (chunk) => {
    child.stderrText += chunk.toString();
  });
  child.on("exit", (code, signal) => {
    child.exitSummary = `${name} exited with ${signal || code}`;
  });
  children.push(child);
  return child;
};

const stopChild = async (child) => {
  if (!child || child.killed) {
    return;
  }
  child.expectedStop = true;
  child.kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => child.once("close", resolve)),
    wait(2000),
  ]);
  if (!child.killed && child.exitCode === null) {
    child.kill("SIGKILL");
  }
};

const waitForOk = async (url, label, attempts = 80) => {
  for (let index = 0; index < attempts; index += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return response;
      }
    } catch {
      // Startup races are expected while the local smoke servers boot.
    }
    await wait(150);
  }
  throw new Error(`${label} did not become ready at ${url}`);
};

const textIncludes = (label, text, expected) => {
  const lower = text.toLowerCase();
  const missing = expected.filter((item) => !lower.includes(item.toLowerCase()));
  if (missing.length) {
    throw new Error(`${label} is missing expected copy: ${missing.join(", ")}. Actual text: ${text.slice(0, 900)}`);
  }
};

const assertNoBrowserErrors = (consoleErrors, pageErrors) => {
  if (consoleErrors.length || pageErrors.length) {
    throw new Error(
      `Browser smoke saw errors:\nconsole=${JSON.stringify(consoleErrors, null, 2)}\npage=${JSON.stringify(pageErrors, null, 2)}`,
    );
  }
};

const clickNav = async (page, label) => {
  await page.locator(".app-nav button", { hasText: label }).click();
};

const api = start("api", "python3", [
  "-m",
  "backend.app.server",
  "--host",
  "127.0.0.1",
  "--port",
  String(apiPort),
  "--db",
  dbPath,
]);

const web = start(
  "web",
  "npm",
  ["run", "dev:web", "--", "--port", String(webPort), "--strictPort"],
  { env: { LOCALPILOT_API_URL: apiUrl } },
);

let browser;

try {
  await waitForOk(`${apiUrl}/api/v1/health`, "Backend");
  await waitForOk(`${webUrl}/app?module=dashboard`, "Vite app");

  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });
  page.on("pageerror", (error) => {
    pageErrors.push(error.message);
  });

  await page.goto(`${webUrl}/app?module=dashboard`, { waitUntil: "networkidle" });
  await page.locator(".content-card-grid article").first().waitFor({ timeout: 10000 });

  const navModules = (await page.locator(".app-nav button").allTextContents()).map((item) => item.trim());
  const expectedModules = [
    "Create New",
    "Auto Posting",
    "Ad Inspirations",
    "Content Library",
    "Content Calendar",
    "Brand & Social Accounts",
    "Competitor Analysis",
    "Analytics",
    "Need help",
  ];
  const missingModules = expectedModules.filter((module) => !navModules.some((item) => item.includes(module)));
  if (missingModules.length) {
    throw new Error(`Phase 3 navigation is missing modules: ${missingModules.join(", ")}`);
  }

  await page.goto(`${webUrl}/app?module=create-new`, { waitUntil: "networkidle" });
  await page.locator(".create-format-grid").waitFor({ timeout: 10000 });
  const createText = await page.locator(".primary-panel").innerText();
  textIncludes("Create New screen", createText, [
    "Create Your Next Post",
    "Image",
    "UGC",
    "Short Ad Video",
    "Carousel",
    "Faceless Video",
    "Product Photo Shoot",
  ]);
  await page.locator(".create-format-grid button", { hasText: "UGC" }).click();
  await page.locator(".creator-workflow-modal").waitFor({ timeout: 10000 });
  textIncludes("Creator workflow modal", await page.locator(".creator-workflow-modal").innerText(), [
    "LocalPilot.ai",
    "Create UGC Video",
    "Write Your Idea",
    "Generate ideas for me",
  ]);
  await page.locator(".creator-style-wizard").waitFor({ timeout: 10000 });
  const creatorWizardText = await page.locator(".creator-style-wizard").innerText();
  textIncludes("Creator-style video wizard", creatorWizardText, [
    "Create UGC Video",
    "Generate ideas for me",
    "Write Your Idea",
    "Continue",
  ]);
  await page.getByRole("button", { name: "Generate ideas for me" }).click();
  await page.locator(".creator-idea-chat").waitFor({ timeout: 10000 });
  textIncludes("Generate ideas chat popup", await page.locator(".creator-idea-chat").innerText(), [
    "Generate ideas for me",
    "What would you like to create",
    "Can you tell me more",
  ]);
  await page.locator(".creator-idea-chat-form input").fill("Generate a practical local offer that drives calls this week.");
  await page.getByRole("button", { name: "Send idea goal" }).click();
  await page.locator(".creator-chat-prompt-results button", { hasText: "Use This Prompt" }).first().waitFor({ timeout: 10000 });
  textIncludes("Generate ideas prompt suggestions", await page.locator(".creator-idea-chat").innerText(), [
    "Here are",
    "Use This Prompt",
  ]);
  await page.locator(".creator-chat-prompt-results button", { hasText: "Use This Prompt" }).first().click();
  await page.locator(".creator-segmented button", { hasText: "Motivational" }).click();
  await page.locator(".creator-wizard-footer .primary-action").click();
  await page.locator(".creator-avatar-grid button").first().click();
  await page.locator(".creator-wizard-footer .primary-action").click();
  await page.locator(".creator-template-grid button").first().click();
  await page.locator(".creator-wizard-footer .primary-action").click();
  textIncludes("Creator review step", await page.locator(".creator-style-wizard").innerText(), [
    "Review your script",
    "Your script",
    "Estimated Duration",
    "Rewrite for 16s",
    "Update your script",
  ]);
  await page.locator(".creator-duration-options button", { hasText: "Rewrite for 16s" }).click();
  await page.locator(".creator-script-rewrite input").fill("Make it warmer and keep the CTA sharper.");
  await page.getByRole("button", { name: "Apply script rewrite" }).click();
  await page.locator(".creator-wizard-footer .primary-action", { hasText: "Continue" }).click();
  textIncludes("Creator confirm details step", await page.locator(".creator-style-wizard").innerText(), [
    "Review and confirm your details",
    "Summary",
    "Post Type: UGC",
    "Aspect Ratio:",
    "Estimated credit usage",
  ]);
  await page.locator(".creator-wizard-footer .primary-action", { hasText: "Generate" }).click();
  await page.locator(".creator-output-panel").waitFor({ timeout: 10000 });
  textIncludes("Creator generated artifacts", await page.locator(".creator-output-panel").innerText(), [
    "creative:",
    "media asset:",
    "UGC package:",
    "calendar slot:",
    "Publish",
    "Schedule Post",
  ]);
  await page.getByRole("button", { name: "Close workflow" }).click();
  await page.getByRole("button", { name: "Back" }).click();
  await page.locator(".create-format-grid").waitFor({ timeout: 10000 });
  await page.locator(".create-format-grid button", { hasText: "Carousel" }).click();
  const carouselText = await page.locator(".carousel-config-panel").innerText();
  textIncludes("Carousel configuration", carouselText, [
    "Storytelling",
    "Promotional",
    "Motivational",
    "Exploratory",
    "1:1",
    "9:16",
    "Brand linked",
  ]);
  await page.locator(".create-flow-footer .primary-action").click();
  await page.locator(".content-card-grid article").first().waitFor({ timeout: 10000 });

  await page.goto(`${webUrl}/app?module=ad-inspirations`, { waitUntil: "networkidle" });
  await page.locator(".inspiration-grid article").first().waitFor({ timeout: 10000 });
  const inspirationText = await page.locator(".primary-panel").innerText();
  textIncludes("Ad Inspirations screen", inspirationText, [
    "Inspirations",
    "Trending collection",
    "UGC Ads",
    "Image Ads",
    "View all",
    "< 8 sec",
    ">= 8 sec",
    "Beauty",
  ]);
  await page.getByRole("button", { name: "View all trending collection" }).click();
  await page.locator(".wait-nudge-modal").waitFor({ timeout: 10000 });
  textIncludes("Wait modal", await page.locator(".wait-nudge-modal").innerText(), [
    "Wait! Don't Go...",
    "first 10 generations are on us",
    "Maybe later",
    "Download a post",
  ]);
  await page.getByRole("button", { name: "Maybe later" }).click();
  textIncludes("Trending collection view", await page.locator(".primary-panel").innerText(), [
    "Trending collection",
    "Travel inspirations",
    "Consumer Electronic",
  ]);
  await page.getByLabel("Back to Inspirations").click();
  await page.locator(".inspiration-ugc .inspiration-grid article").first().getByRole("button", { name: "Recreate" }).click();
  await page.locator(".creator-workflow-modal").waitFor({ timeout: 10000 });
  await page.locator(".creator-style-wizard").waitFor({ timeout: 10000 });
  textIncludes("Inspiration to creator wizard", await page.locator(".creator-workflow-modal").innerText(), [
    "Create UGC Video",
    "Write Your Idea",
    "Generate ideas for me",
  ]);
  await page.getByRole("button", { name: "Close workflow" }).click();

  await clickNav(page, "Content Library");
  await page.locator(".library-filter-panel").waitFor({ timeout: 10000 });
  await page.locator(".type-tab-row button", { hasText: "Video" }).click();
  const libraryText = await page.locator(".primary-panel").innerText();
  textIncludes("Content Library screen", libraryText, [
    "Content Library",
    "All",
    "Image",
    "Video",
    "Carousel",
    "Remove Watermark",
    "Publish",
  ]);
  const firstLibraryCard = page.locator(".content-card-grid article").first();
  const firstLibraryCardText = await firstLibraryCard.innerText();
  if (firstLibraryCardText.toLowerCase().includes("great things take time")) {
    throw new Error(`First Content Library card is still masked by the cooking overlay: ${firstLibraryCardText.slice(0, 500)}`);
  }
  await firstLibraryCard.locator(".library-play-button").waitFor({ timeout: 10000 });
  await firstLibraryCard.locator(".library-edit-pencil").waitFor({ timeout: 10000 });
  await firstLibraryCard.locator(".library-play-button").click();
  await page.locator(".library-detail-modal").waitFor({ timeout: 10000 });
  textIncludes("Content Library asset detail overlay", await page.locator(".library-detail-modal").innerText(), [
    "from your idea",
    "credits used",
    "Caption",
    "Input Prompt:",
    "Would you use this post?",
    "Publish",
    "Edit",
    "Download",
  ]);
  await page.locator(".library-detail-actions button", { hasText: "Publish" }).click();
  await page.locator(".publish-modal").waitFor({ timeout: 10000 });
  const facebookPublishText = await page.locator(".publish-modal").innerText();
  textIncludes("Publish modal warnings", facebookPublishText, [
    "Publish post",
    "Ready to post",
    "Facebook",
    "Facebook Reel",
    "Accounts",
    "Link account",
  ]);
  await page.locator(".publish-ready-panel button", { hasText: "Facebook Reel" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  const scheduleText = await page.locator(".publish-modal").innerText();
  textIncludes("Publish modal schedule confirmation", scheduleText, [
    "Schedule post",
    "June 2026",
    "America/Detroit",
    "Apply AI suggested time",
    "Select Team Member for approval",
    "Schedule Post",
  ]);
  await page.locator(".publish-schedule-check").first().click();
  await page.locator(".publish-schedule-actions button", { hasText: "Schedule Post" }).click();
  await page.locator(".publish-modal").waitFor({ state: "hidden", timeout: 10000 });
  await page.locator(".calendar-board").waitFor({ timeout: 10000 });
  await page.locator(".calendar-post-card").first().waitFor({ timeout: 10000 });
  await page.getByRole("button", { name: "Monthly" }).click();
  await page.getByRole("button", { name: "Today" }).click();
  await page.locator(".calendar-footer select").selectOption({ label: "America/Detroit" });
  await page.locator(".calendar-day.has-post").first().click();
  await page.locator(".calendar-detail-drawer").waitFor({ timeout: 10000 });
  const calendarText = await page.locator(".calendar-workbench").innerText();
  textIncludes("Content Calendar parity", calendarText, [
    "June 2026",
    "Select Timezone",
    "Published",
    "Scheduled",
    "Failed",
    "Rejected",
    "In Review",
    "Scheduled post detail drawer",
    "Locked near publish",
    "Discard",
    "Reschedule",
  ]);
  await page.getByRole("button", { name: "Reschedule" }).last().click();
  await page.waitForTimeout(400);

  await clickNav(page, "Brand & Social Accounts");
  await page.locator(".brand-account-tabs").waitFor({ timeout: 10000 });
  const accountsText = await page.locator(".predis-surface").innerText();
  textIncludes("Brand & Social Accounts social tab", accountsText, [
    "Social Platforms",
    "Instagram",
    "Business or Creator accounts",
    "Facebook",
    "Watch Videos",
    "FAQ",
    "Add",
    "Unlink",
    "Google Business Profile",
    "TikTok",
  ]);
  await page.locator(".social-connected-card").waitFor({ timeout: 10000 });
  const instagramRow = page.locator(".social-platform-grid article", { hasText: "Instagram" });
  await instagramRow.getByRole("button", { name: /FAQ/ }).click();
  textIncludes("Instagram FAQ modal", await page.locator(".social-action-modal").innerText(), [
    "Instagram FAQ's",
    "I am trying to Link Instagram",
    "I have an Instagram creator account",
  ]);
  await page.getByLabel("Close social account dialog").click();
  await instagramRow.getByRole("button", { name: "Add" }).click();
  textIncludes("Instagram Add modal", await page.locator(".social-action-modal").innerText(), [
    "Connect your Instagram account",
    "Professional",
    "via Facebook",
    "via Instagram",
    "NEW",
  ]);
  await page.getByLabel("Close social account dialog").click();
  await instagramRow.getByRole("button", { name: /Watch Videos/ }).click();
  textIncludes("Instagram videos modal", await page.locator(".social-action-modal").innerText(), [
    "Instagram Videos",
    "How to connect Instagram",
  ]);
  await page.getByLabel("Close social account dialog").click();
  await page.locator(".social-platform-grid article", { hasText: "TikTok" }).getByRole("button", { name: /FAQ/ }).click();
  textIncludes("TikTok FAQ modal", await page.locator(".social-action-modal").innerText(), [
    "TikTok FAQ's",
    "Will my video get published automatically to TikTok?",
  ]);
  await page.getByLabel("Close social account dialog").click();
  const brandTabs = (await page.locator(".brand-account-tabs button").allTextContents()).map((item) => item.trim());
  if (brandTabs.includes("Style")) {
    throw new Error(`Brand & Social Accounts should not expose Style as a top-level tab: ${brandTabs.join(", ")}`);
  }
  await page.locator(".brand-account-tabs button", { hasText: "Brand Details" }).click();
  textIncludes("Brand Details tab", await page.locator(".predis-surface").innerText(), [
    "Business identity",
    "Style",
    "Content settings",
    "Tonality of Communication",
    "Select Timezone",
    "(GMT -4:00) America/Detroit",
    "Brand Ethnicity",
    "Brand Voiceover",
    "AI Media",
    "Brand Avatar",
  ]);
  await page.locator(".brand-details-inner-nav button", { hasText: "Business identity" }).click();
  textIncludes("Brand Details business identity section", await page.locator(".predis-surface").innerText(), [
    "Business name",
    "Website",
    "Social handle",
    "Hashtags",
    "Fetch details from website",
  ]);
  await page.locator(".brand-details-inner-nav button", { hasText: "Style" }).click();
  textIncludes("Brand Details style section", await page.locator(".predis-surface").innerText(), [
    "Title typography",
    "Subtitle typography",
    "Light logo",
    "Dark logo",
    "Font colors",
  ]);
  await page.locator(".brand-details-inner-nav button", { hasText: "Content settings" }).click();
  await page.locator(".brand-account-tabs button", { hasText: "Integrations" }).click();
  textIncludes("Integrations tab", await page.locator(".predis-surface").innerText(), [
    "Integrations",
    "Connect your online store and link your products.",
    "Used by over 20,000+",
    "Rated 4.8",
    "Verified by",
    "Shopify",
    "Wix",
    "Squarespace",
    "WooComm...",
    "Connect",
    "Other E-Commerce Platforms",
    "Download Sample",
    "Click to upload",
    "or drag and drop",
  ]);
  await page.locator(".ecommerce-connector-grid button", { hasText: "Connect" }).first().click();
  await page.locator(".brand-account-tabs button", { hasText: "Exports" }).click();
  textIncludes("Exports tab", await page.locator(".predis-surface").innerText(), [
    "Exports",
    "View, download, and reuse all the posts you've created.",
    "Description",
    "Dimension",
    "Status",
    "Create a UGC video for an on-camera founder exp...",
    "Midea 9,000 BTU Mini Split AC/Heating System",
    "Portrait (720×1264)",
    "Processing complete",
  ]);
  await page.locator(".exports-table-row").first().getByRole("button", { name: /Download/ }).click();

  await clickNav(page, "Competitor Analysis");
  await page.locator(".competitor-link-gate").waitFor({ timeout: 10000 });
  const competitorText = await page.locator(".predis-surface").innerText();
  textIncludes("Competitor Analysis account gate", competitorText, [
    "Please link Your Accounts to start using Competitor Analysis",
    "Instagram - Business or Creator Account",
    "Facebook connection required",
    "Link now",
    "LocalPilot advanced demo",
    "Analyze a saved source",
  ]);
  await page.getByRole("button", { name: "Link now" }).click();
  textIncludes("Competitor Analysis link now modal", await page.locator(".social-action-modal").innerText(), [
    "Connect your Instagram account",
    "via Facebook",
    "via Instagram",
  ]);
  await page.getByLabel("Close social account dialog").click();

  await clickNav(page, "Analytics");
  await page.locator(".performance-dashboard").waitFor({ timeout: 10000 });
  const analyticsText = await page.locator(".analytics-workspace").innerText();
  textIncludes("Analytics parity plus proof", analyticsText, [
    "Post consistency",
    "Day streak",
    "Instagram",
    "Aurora Heating & Cooling",
    "LinkedIn",
    "New posts",
    "Followers",
    "Engagement",
    "Your Posting Activity",
    "Your Posts' Engagement",
    "Your Followers' Growth",
    "Lower-bound evidence",
    "not fake exact ROI",
    "Record demo event",
  ]);
  await page.locator(".roi-signal-grid article button").first().click();
  await page.waitForTimeout(400);

  await clickNav(page, "Need help");
  await page.locator(".sidebar-help-flyout").waitFor({ timeout: 10000 });
  textIncludes("Need help sidebar flyout", await page.locator(".app-sidebar").innerText(), [
    "Need a hand?",
    "Chat Support",
    "Book a Demo",
  ]);
  textIncludes("Analytics remains visible behind help flyout", await page.locator(".analytics-workspace").innerText(), [
    "Posting activity",
    "Post engagement",
    "Follower growth",
  ]);
  await page.locator(".sidebar-help-flyout").getByRole("button", { name: "Chat Support" }).click();
  await page.waitForTimeout(400);

  assertNoBrowserErrors(consoleErrors, pageErrors);

  console.log(
    JSON.stringify(
      {
        ok: true,
        modules: navModules,
        checked: [
          "Predis-reference navigation labels",
          "Create New format cards and creator-style video wizard",
          "Carousel pre-generation configuration",
          "Inspirations recreate-to-wizard flow",
          "Content Library filters, cards, cooking state, publish modal gating",
          "Calendar weekly/monthly controls, timezone, legend, detail drawer",
          "Brand & Social Accounts tabs, social action dialogs, and Facebook page picker",
          "Competitor Analysis account-link gate and Link now social dialog",
          "Analytics streak, empty states, and LocalPilot proof loop",
          "Need Help sidebar flyout without leaving Analytics",
        ],
      },
      null,
      2,
    ),
  );
} finally {
  if (browser) {
    await browser.close();
  }
  await Promise.all(children.map((child) => stopChild(child)));
  await rm(tempDir, { recursive: true, force: true });
  const failed = children.filter((child) => !child.expectedStop && child.exitCode && child.exitCode !== 0);
  if (failed.length) {
    for (const child of failed) {
      console.error(child.exitSummary || "child failed");
      if (child.stderrText) {
        console.error(child.stderrText);
      }
      if (child.stdoutText) {
        console.error(child.stdoutText);
      }
    }
  }
}
