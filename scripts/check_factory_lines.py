"""Check factory lines in UI."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Go to factories page
    page.goto("http://localhost:3010/factories")
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)

    # Take screenshot of the list
    page.screenshot(path="d:/KobetsuV1.0/outputs/factories_list.png", full_page=True)
    print("Screenshot saved: factories_list.png")

    # Try to find and click on Takao Kainan factory
    # First, let's search or filter
    search_input = page.locator('input[placeholder*="検索"]').first
    if search_input.count() > 0:
        search_input.fill("高雄")
        page.wait_for_timeout(1000)
        page.screenshot(path="d:/KobetsuV1.0/outputs/factories_takao.png", full_page=True)
        print("Screenshot saved: factories_takao.png")

    browser.close()
