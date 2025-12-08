"""
Test editing and deleting a line
"""
import asyncio
from playwright.async_api import async_playwright

async def test_edit_delete():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Handle dialogs
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

        print("1. Navigating to factory 39...")
        await page.goto("http://localhost:3011/factories/39")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Click on Test-001 line to expand
        print("\n2. Clicking on Test-001 to expand...")
        test_line = await page.query_selector("text=Test-001")
        if test_line:
            await test_line.click()
            await asyncio.sleep(1)
            await page.screenshot(path="edit_1_expanded.png")
            print("   Screenshot saved: edit_1_expanded.png")

            # Click edit button
            print("\n3. Clicking edit button...")
            edit_btn = await page.query_selector("button:has-text('編集')")
            if edit_btn:
                # Need to get the last edit button (within the expanded section)
                edit_buttons = await page.query_selector_all("button:has-text('編集')")
                if len(edit_buttons) > 1:
                    await edit_buttons[-1].click()
                    await asyncio.sleep(1)
                    await page.screenshot(path="edit_2_modal.png")
                    print("   Screenshot saved: edit_2_modal.png")

                    # Modify the supervisor name
                    print("\n4. Modifying supervisor name...")
                    supervisor_input = await page.query_selector("input[name='supervisor_name']")
                    if supervisor_input:
                        await supervisor_input.fill("テスト課長 編集済み")

                    await page.screenshot(path="edit_3_modified.png")
                    print("   Screenshot saved: edit_3_modified.png")

                    # Submit using JavaScript
                    print("\n5. Submitting form...")
                    await page.evaluate("document.querySelector('form').requestSubmit()")
                    await asyncio.sleep(3)

                    await page.screenshot(path="edit_4_saved.png")
                    print("   Screenshot saved: edit_4_saved.png")

                    # Verify change
                    print("\n6. Verifying change...")
                    modified_text = await page.query_selector("text=テスト課長 編集済み")
                    if modified_text:
                        print("   SUCCESS! Line was modified!")
                    else:
                        # Expand the line again to check
                        test_line2 = await page.query_selector("text=Test-001")
                        if test_line2:
                            await test_line2.click()
                            await asyncio.sleep(1)
                            await page.screenshot(path="edit_5_verify.png")
                            print("   Screenshot saved: edit_5_verify.png")

        print("\n7. Now testing delete...")
        # Navigate fresh
        await page.goto("http://localhost:3011/factories/39")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Expand Test line
        test_line = await page.query_selector("text=Test-001")
        if test_line:
            await test_line.click()
            await asyncio.sleep(1)

            # Find delete button
            delete_buttons = await page.query_selector_all("button:has-text('削除')")
            if len(delete_buttons) > 1:
                print("   Clicking delete button...")
                await delete_buttons[-1].click()
                await asyncio.sleep(2)

                await page.screenshot(path="edit_6_after_delete.png")
                print("   Screenshot saved: edit_6_after_delete.png")

                # Check if line is gone
                test_line_after = await page.query_selector("text=Test-001")
                if not test_line_after:
                    print("   SUCCESS! Line was deleted!")
                else:
                    print("   Line still visible (may be soft deleted)")

        await browser.close()
        print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_edit_delete())
