"""
Playwright test script to verify factory line editing functionality
"""
import asyncio
from playwright.async_api import async_playwright

async def test_factory_lines():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("1. Navigating to factories page...")
        await page.goto("http://localhost:3011/factories")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)

        # Take screenshot of factories list
        await page.screenshot(path="screenshot_1_factories_list.png")
        print("   Screenshot saved: screenshot_1_factories_list.png")

        # Look for factory rows - click on the factory name link
        factory_link = await page.query_selector("a:has-text('恵那工場')")
        if not factory_link:
            # Try clicking on the row itself
            factory_link = await page.query_selector("text=恵那工場")

        if factory_link:
            print("\n2. Found factory '恵那工場', clicking...")
            await factory_link.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Take screenshot of factory detail
            await page.screenshot(path="screenshot_2_factory_detail.png")
            print("   Screenshot saved: screenshot_2_factory_detail.png")

            # Check current URL
            current_url = page.url
            print(f"   Current URL: {current_url}")

            # Look for the lines section
            lines_section = await page.query_selector("text=配属先・ライン情報")
            if lines_section:
                print("   Found lines section!")
                await lines_section.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                await page.screenshot(path="screenshot_3_lines_section.png")
                print("   Screenshot saved: screenshot_3_lines_section.png")

                # Look for "新規ライン追加" button
                add_line_btn = await page.query_selector("button:has-text('新規ライン追加')")
                if not add_line_btn:
                    add_line_btn = await page.query_selector("text=新規ライン追加")

                if add_line_btn:
                    print("\n3. Found 'Add new line' button, clicking...")
                    await add_line_btn.click()
                    await asyncio.sleep(1)

                    # Take screenshot of modal
                    await page.screenshot(path="screenshot_4_new_line_modal.png")
                    print("   Screenshot saved: screenshot_4_new_line_modal.png")

                    # Check if modal opened
                    modal_title = await page.query_selector("text=新規ライン作成")
                    if modal_title:
                        print("   Modal opened successfully!")

                        # Fill in some test data
                        print("\n4. Filling in test data...")

                        # Fill line_id
                        line_id_input = await page.query_selector("input[name='line_id']")
                        if line_id_input:
                            await line_id_input.fill("Test-Line-001")
                            print("   Filled line_id")

                        # Fill department
                        dept_input = await page.query_selector("input[name='department']")
                        if dept_input:
                            await dept_input.fill("テスト製造部")
                            print("   Filled department")

                        # Fill line_name
                        line_name_input = await page.query_selector("input[name='line_name']")
                        if line_name_input:
                            await line_name_input.fill("テストライン1課")
                            print("   Filled line_name")

                        # Fill supervisor_name
                        supervisor_input = await page.query_selector("input[name='supervisor_name']")
                        if supervisor_input:
                            await supervisor_input.fill("課長 テスト太郎")
                            print("   Filled supervisor_name")

                        # Fill hourly_rate
                        rate_input = await page.query_selector("input[name='hourly_rate']")
                        if rate_input:
                            await rate_input.fill("1500")
                            print("   Filled hourly_rate")

                        await page.screenshot(path="screenshot_5_filled_form.png")
                        print("   Screenshot saved: screenshot_5_filled_form.png")

                        # Click save button
                        print("\n5. Clicking save button...")

                        # Handle dialog before clicking
                        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

                        # Submit form using requestSubmit which triggers React's onSubmit
                        await page.evaluate("""
                            const form = document.querySelector('form');
                            if (form) {
                                form.requestSubmit();
                            }
                        """)
                        await asyncio.sleep(3)

                        await page.screenshot(path="screenshot_6_after_save.png")
                        print("   Screenshot saved: screenshot_6_after_save.png")

                        # Check if we're back on the detail page with the new line
                        await asyncio.sleep(1)
                        await page.screenshot(path="screenshot_7_final.png")
                        print("   Screenshot saved: screenshot_7_final.png")

                        # Look for the newly created line
                        new_line = await page.query_selector("text=テスト製造部")
                        if new_line:
                            print("\n   SUCCESS! New line 'テスト製造部' was created!")
                        else:
                            print("\n   Line may have been created - check screenshots")
                    else:
                        print("   Modal did not open!")
                else:
                    print("   'Add new line' button not found!")
                    # Debug: list all buttons
                    buttons = await page.query_selector_all("button")
                    print(f"   Found {len(buttons)} buttons")
            else:
                print("   Lines section not found!")
        else:
            print("   Factory '恵那工場' not found, trying to scroll...")
            await page.screenshot(path="screenshot_debug.png")

        print("\n6. Test completed!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_factory_lines())
