"""Quick verification script to check factory count in UI."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Go to import page
    page.goto("http://localhost:3010/import")
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1000)  # Extra wait for React Query to fetch

    # Take screenshot
    page.screenshot(path="d:/KobetsuV1.0/outputs/verify_import.png", full_page=True)
    print("Screenshot saved: verify_import.png")

    # Try to get factory count from the green card
    factory_cards = page.locator('.bg-green-500').all()
    for card in factory_cards:
        parent = card.locator('..')
        count = parent.locator('.text-3xl').text_content()
        print(f"Factory count displayed: {count}")

    browser.close()
