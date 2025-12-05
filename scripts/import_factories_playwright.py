"""
Playwright script to import factory JSON files from E:\factories
into the Kobetsu system via the web interface.
"""
import os
import glob
from playwright.sync_api import sync_playwright

# Configuration
FACTORIES_DIR = r"E:\factories"
FRONTEND_URL = "http://localhost:3010"

def get_json_files(directory: str) -> list[str]:
    """Get all JSON files from the factories directory."""
    pattern = os.path.join(directory, "*.json")
    files = glob.glob(pattern)
    # Exclude mapping files
    files = [f for f in files if "mapping" not in os.path.basename(f).lower()]
    return sorted(files)

def main():
    json_files = get_json_files(FACTORIES_DIR)
    print(f"Found {len(json_files)} JSON files to import")

    if not json_files:
        print("No JSON files found!")
        return

    # Show files to import (with proper encoding)
    for i, f in enumerate(json_files[:5], 1):
        print(f"  {i}. {os.path.basename(f)}")
    if len(json_files) > 5:
        print(f"  ... and {len(json_files) - 5} more")

    with sync_playwright() as p:
        # Launch browser (headless for automation)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print(f"\nNavigating to {FRONTEND_URL}/import ...")
        page.goto(f"{FRONTEND_URL}/import")
        page.wait_for_load_state('networkidle')

        # Take screenshot to see initial state
        page.screenshot(path="d:/KobetsuV1.0/outputs/import_01_initial.png")
        print("Screenshot saved: import_01_initial.png")

        # Click on Import tab (the first one in the tab bar with the icon)
        # Use more specific selector - the tab button in the border-b div
        import_tab = page.locator('div.flex.border-b button').filter(has_text="インポート").first
        if import_tab.count() > 0:
            import_tab.click()
            page.wait_for_timeout(500)

        # Select factories import type (工場マスタ) - it's a toggle button
        # Look for the button with the factory icon
        factories_btn = page.locator('button').filter(has_text="工場マスタ").first
        if factories_btn.count() > 0:
            factories_btn.click()
            page.wait_for_timeout(500)
            print("Selected: 工場マスタ (factories)")

        page.screenshot(path="d:/KobetsuV1.0/outputs/import_02_factories_selected.png")

        # Find the file input and upload all JSON files
        file_input = page.locator('input[type="file"]')

        if file_input.count() > 0:
            print(f"\nUploading {len(json_files)} files...")
            # Upload all files at once
            file_input.set_input_files(json_files)

            # Wait for processing
            page.wait_for_timeout(2000)
            page.screenshot(path="d:/KobetsuV1.0/outputs/import_03_files_uploaded.png")
            print("Files uploaded, screenshot saved: import_03_files_uploaded.png")

            # Look for batch import button
            batch_btn = page.locator('button:has-text("一括インポート")')
            if batch_btn.count() > 0 and batch_btn.is_visible():
                print("Clicking batch import button...")
                batch_btn.click()

                # Wait for import to complete (may take a while)
                page.wait_for_timeout(10000)

                # Handle any alert that appears
                page.on("dialog", lambda dialog: dialog.accept())

                page.screenshot(path="d:/KobetsuV1.0/outputs/import_04_batch_complete.png")
                print("Batch import completed, screenshot saved: import_04_batch_complete.png")
            else:
                # Try single file import flow
                execute_btn = page.locator('button:has-text("インポート実行")')
                if execute_btn.count() > 0 and execute_btn.is_visible():
                    print("Clicking import execute button...")
                    execute_btn.click()
                    page.wait_for_timeout(5000)
                    page.screenshot(path="d:/KobetsuV1.0/outputs/import_04_execute_complete.png")
                    print("Import executed, screenshot saved: import_04_execute_complete.png")
                else:
                    print("No import button found - checking page state...")
                    page.screenshot(path="d:/KobetsuV1.0/outputs/import_04_no_button.png")
        else:
            print("File input not found!")
            page.screenshot(path="d:/KobetsuV1.0/outputs/import_error.png")

        # Final state - go to overview to see counts
        overview_tab = page.locator('button:has-text("データ概要")')
        if overview_tab.count() > 0:
            overview_tab.click()
            page.wait_for_timeout(1000)
            page.screenshot(path="d:/KobetsuV1.0/outputs/import_05_final_overview.png")
            print("Final overview screenshot saved: import_05_final_overview.png")

        # Get the factory count from the page
        factory_count = page.locator('.bg-green-500').locator('..').locator('.text-3xl')
        if factory_count.count() > 0:
            count_text = factory_count.text_content()
            print(f"\nFactory count in UI: {count_text}")

        browser.close()
        print("\nDone!")

if __name__ == "__main__":
    main()
