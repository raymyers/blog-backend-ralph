import { test, expect } from "@playwright/test";
import { registerUser, createArticle } from "./helpers";

// Block slow external CDN resources so page.goto doesn't hang on load event
test.beforeEach(async ({ page }) => {
  await page.route(
    /(code\.ionicframework\.com|fonts\.googleapis\.com|fonts\.gstatic\.com)/,
    (route) => route.abort()
  );
});

// Helper: inject auth token into localStorage (SPA stores just 'jwtToken')
async function injectAuth(
  page: import("@playwright/test").Page,
  token: string,
  _username: string
) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.evaluate((t) => localStorage.setItem("jwtToken", t), token);
}

// ── Navigation & Layout ─────────────────────────────────────

test.describe("Layout & Navigation", () => {
  test("home page loads with navbar and banner", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.locator("nav .navbar-brand")).toHaveText("conduit");
    await expect(page.locator(".home-page .banner h1")).toBeVisible();
  });

  test("navbar shows auth links when logged out", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.evaluate(() => localStorage.clear());
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(500);
    await expect(page.locator("nav.navbar")).toContainText("Home");
    await expect(page.locator("nav.navbar")).toContainText("Sign in");
    await expect(page.locator("nav.navbar")).toContainText("Sign up");
  });

  test("footer is present", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.locator("footer")).toBeVisible();
    await expect(page.locator("footer")).toContainText("conduit");
  });
});

// ── Authentication ──────────────────────────────────────────

test.describe("Authentication", () => {
  const unique = Date.now();

  test("register new user via UI", async ({ page }) => {
    await page.goto("/register", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(300);
    await page.fill('input[name="username"]', `pw_user_${unique}`);
    await page.fill('input[name="email"]', `pw${unique}@test.com`);
    await page.fill('input[name="password"]', "password123");
    await page.click('button:has-text("Sign up")');
    await page.waitForTimeout(1500);
    await expect(page.locator("nav.navbar")).toContainText(`pw_user_${unique}`);
  });

  test("login existing user via UI", async ({ page }) => {
    const u = `login_${unique}`;
    await registerUser(u, `${u}@test.com`, "password123");
    await page.goto("/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(300);
    await page.fill('input[name="email"]', `${u}@test.com`);
    await page.fill('input[name="password"]', "password123");
    await page.click('button:has-text("Sign in")');
    await page.waitForTimeout(1500);
    await expect(page.locator("nav.navbar")).toContainText(u);
  });

  test("login with wrong password stays on login page", async ({ page }) => {
    await page.goto("/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(300);
    await page.fill('input[name="email"]', "nobody@nowhere.com");
    await page.fill('input[name="password"]', "wrongpw");
    await page.click('button:has-text("Sign in")');
    await page.waitForTimeout(1500);
    // Should NOT show authenticated nav items
    await expect(page.locator("nav.navbar")).not.toContainText("Settings");
  });
});

// ── Article CRUD ────────────────────────────────────────────

test.describe("Articles", () => {
  const unique = Date.now();
  let token: string;
  const username = `author_${unique}`;

  test.beforeAll(async () => {
    token = await registerUser(username, `${username}@test.com`, "pw123");
  });

  test("global feed shows articles", async ({ page }) => {
    await createArticle(token, `E2E Article ${unique}`, "desc", "body text", [
      "e2e",
    ]);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(800);
    await expect(page.locator(".article-preview").first()).toBeVisible();
    await expect(page.locator("body")).toContainText(`E2E Article ${unique}`);
  });

  test("article detail page", async ({ page }) => {
    const { slug } = await createArticle(
      token,
      `Detail ${unique}`,
      "test desc",
      "Full article body here",
      ["detail"]
    );
    await page.goto(`/article/${slug}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(800);
    await expect(page.locator(".article-page h1")).toContainText(
      `Detail ${unique}`
    );
    await expect(page.locator(".article-content").first()).toContainText(
      "Full article body here"
    );
  });

  test("create article via editor UI", async ({ page }) => {
    await injectAuth(page, token, username);
    await page.goto("/editor", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(500);
    const title = `UI Article ${unique}`;
    await page.fill('input[name="title"]', title);
    await page.fill('input[name="description"]', "About testing");
    await page.fill('textarea[name="body"]', "Article body written in the editor.");
    await page.click('button:has-text("Publish")');
    await page.waitForTimeout(2000);
    await expect(page.locator("body")).toContainText(title);
  });
});

// ── Tags ────────────────────────────────────────────────────

test.describe("Tags", () => {
  test("tags sidebar shows on home page", async ({ page }) => {
    const ts = Date.now();
    const tok = await registerUser(`tagger_${ts}`, `tagger_${ts}@test.com`, "pw");
    await createArticle(tok, "Tag Test 1", "d", "b", ["alphaTag"]);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(800);
    await expect(page.locator(".sidebar")).toBeVisible();
    await expect(page.locator(".sidebar")).toContainText("Popular Tags");
  });
});

// ── Profile ─────────────────────────────────────────────────

test.describe("Profile", () => {
  const unique = Date.now();
  let token: string;
  const username = `profile_${unique}`;

  test.beforeAll(async () => {
    token = await registerUser(username, `${username}@test.com`, "pw123");
    await createArticle(token, `Profile Article ${unique}`, "d", "b");
  });

  test("profile page shows username and articles", async ({ page }) => {
    await page.goto(`/profile/${username}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(800);
    await expect(page.locator("body")).toContainText(username);
    await expect(page.locator("body")).toContainText(
      `Profile Article ${unique}`
    );
  });
});

// ── Comments ────────────────────────────────────────────────

test.describe("Comments", () => {
  const unique = Date.now();
  let token: string;
  let slug: string;
  const username = `commenter_${unique}`;

  test.beforeAll(async () => {
    token = await registerUser(username, `${username}@test.com`, "pw123");
    const result = await createArticle(
      token,
      `Comment Article ${unique}`,
      "d",
      "b"
    );
    slug = result.slug;
  });

  test("post a comment via UI", async ({ page }) => {
    await injectAuth(page, token, username);
    await page.goto(`/article/${slug}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(800);
    await page.fill("#comment-body", "Great article!");
    await page.click("#post-comment-btn");
    await page.waitForTimeout(1500);
    await expect(page.locator(".card .card-block").last()).toContainText(
      "Great article!"
    );
  });
});

// ── Settings ────────────────────────────────────────────────

test.describe("Settings", () => {
  const unique = Date.now();
  let token: string;
  const username = `settings_${unique}`;

  test.beforeAll(async () => {
    token = await registerUser(username, `${username}@test.com`, "pw123");
  });

  test("settings page shows user form", async ({ page }) => {
    await injectAuth(page, token, username);
    await page.goto("/settings", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(800);
    await expect(page.locator(".settings-page h1").first()).toContainText(
      "Your Settings"
    );
    await expect(page.locator('input[name="username"]')).toBeVisible();
  });
});

// ── Favorites ───────────────────────────────────────────────

test.describe("Favorites", () => {
  const unique = Date.now();
  let token: string;
  const username = `fav_${unique}`;

  test.beforeAll(async () => {
    token = await registerUser(username, `${username}@test.com`, "pw123");
    await createArticle(token, `Fav Article ${unique}`, "d", "b");
  });

  test("favorite button shows count", async ({ page }) => {
    await injectAuth(page, token, username);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(800);
    const favBtn = page.locator("button[data-fav]").first();
    await expect(favBtn).toBeVisible();
  });
});
