"""
Final test - verify modal buttons are accessible
"""
import asyncio
from playwright.async_api import async_playwright

async def test_final():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Handle dialogs
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

        print("1. Navigating to factory 39...")
        await page.goto("http://localhost:3011/factories/39")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

        # Click add new line button
        print("\n2. Opening add new line modal...")
        add_btn = await page.query_selector("button:has-text('新規ライン追加')")
        if add_btn:
            await add_btn.click()
            await asyncio.sleep(2)
            await page.screenshot(path="final_1_modal.png")
            print("   Screenshot: final_1_modal.png")

            # Fill basic data
            print("\n3. Filling form...")
            await page.fill("input[name='line_id']", "Final-Test-001")
            await page.fill("input[name='department']", "最終テスト部")
            await page.fill("input[name='line_name']", "テストライン")
            await page.fill("input[name='supervisor_name']", "テスト責任者")
            await page.fill("input[name='hourly_rate']", "1800")

            await page.screenshot(path="final_2_filled.png")
            print("   Screenshot: final_2_filled.png")

            # Try clicking save button
            print("\n4. Clicking save button...")
            try:
                save_btn = page.locator("button[type='submit']")
                await save_btn.click(timeout=5000)
                print("   Click succeeded!")
            except Exception as e:
                print(f"   Click failed: {e}")
                # Try force click
                try:
                    await save_btn.click(force=True, timeout=5000)
                    print("   Force click succeeded!")
                except Exception as e2:
                    print(f"   Force click also failed: {e2}")

            await asyncio.sleep(3)
            await page.screenshot(path="final_3_after_save.png")
            print("   Screenshot: final_3_after_save.png")

        await browser.close()
        print("\nDone!")

if __name__ == "__main__":
    asyncio.run(test_final())
