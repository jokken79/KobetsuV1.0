"""
Verify lines are visible in the browser
"""
import asyncio
from playwright.async_api import async_playwright

async def verify_lines():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("1. Navigating to factory 39...")
        await page.goto("http://localhost:3011/factories/39")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

        await page.screenshot(path="verify_1_factory_detail.png", full_page=True)
        print("   Screenshot saved: verify_1_factory_detail.png")

        # Look for lines section
        lines_section = await page.query_selector("text=配属先・ライン情報")
        if lines_section:
            print("   Found lines section!")
            await lines_section.scroll_into_view_if_needed()
            await asyncio.sleep(1)
            await page.screenshot(path="verify_2_lines_section.png", full_page=True)
            print("   Screenshot saved: verify_2_lines_section.png")

            # Check for the test line
            test_line = await page.query_selector("text=Test-001")
            if test_line:
                print("   SUCCESS! Found Test-001 line!")
            else:
                print("   Test-001 not visible yet, checking other lines...")

            # Count lines
            line_items = await page.query_selector_all(".divide-y > div")
            print(f"   Found {len(line_items)} line items")

        await browser.close()
        print("\nDone!")

if __name__ == "__main__":
    asyncio.run(verify_lines())
