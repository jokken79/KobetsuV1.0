"""Check the import tab UI."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("http://localhost:3010/import")
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1000)

    # Click on Import tab
    import_tab = page.locator('button').filter(has_text="インポート").first
    if import_tab.count() > 0:
        import_tab.click()
        page.wait_for_timeout(500)

    # Click on factories button
    factories_btn = page.locator('button').filter(has_text="工場マスタ").first
    if factories_btn.count() > 0:
        factories_btn.click()
        page.wait_for_timeout(500)

    # Take screenshot
    page.screenshot(path="d:/KobetsuV1.0/outputs/import_tab_check.png", full_page=True)
    print("Screenshot saved: import_tab_check.png")

    browser.close()
