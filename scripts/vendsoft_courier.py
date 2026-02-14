"""
Automated Vendsoft Transaction Log Courier
Logs into Vendsoft, downloads YTD transaction log, and uploads to dashboard
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import requests
from playwright.sync_api import sync_playwright
import time
from dotenv import load_dotenv

# Load environment variables from .env.local
env_file = Path(__file__).parent.parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)

# Configuration
VENDSOFT_URL = "https://www.vendsoft.com/"
VENDSOFT_USER = os.getenv("VENDSOFT_USER")
VENDSOFT_PASS = os.getenv("VENDSOFT_PASS")
UPLOAD_ENDPOINT = os.getenv("UPLOAD_ENDPOINT", "https://smart-vending-atx-dashboard.vercel.app/api/upload")

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def fetch_transaction_log():
    """
    Login to Vendsoft and download the YTD transaction log
    Returns: Path to downloaded file or None if failed
    """
    log("Starting Vendsoft login...")

    if not VENDSOFT_USER or not VENDSOFT_PASS:
        log("ERROR: VENDSOFT_USER or VENDSOFT_PASS not set in environment")
        return None

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to Vendsoft
            log(f"Navigating to {VENDSOFT_URL}")
            page.goto(VENDSOFT_URL, timeout=60000)

            # Wait for page to load
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)

            # Check if we're already logged in or need to login
            if page.query_selector('input[id="email"]'):
                log("Login page detected - entering credentials...")
                page.fill('input[id="email"]', VENDSOFT_USER)
                page.fill('input[id="password"]', VENDSOFT_PASS)
                page.click('button[type="submit"]')
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                log("Login successful!")
            elif "login" not in page.url.lower():
                log("Already logged in - proceeding to app...")
            else:
                log("ERROR: Login page detected but email field not found")
                return None

            # Navigate to the actual app (not marketing site)
            log("Navigating to Vendsoft app...")
            page.goto("https://secure.vendsoft.com/next", timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(5)  # Give React time to render

            # Navigate to Reports > Transaction Log
            log("Navigating to Transaction Log report...")

            # Log all visible text on the page to find Reports
            log("Looking for Reports menu...")
            all_text_elements = page.query_selector_all('a, button, span, div')
            log(f"Found {len(all_text_elements)} elements")
            log("Elements containing 'Report':")
            for elem in all_text_elements[:50]:
                text = elem.inner_text().strip()
                if text and 'report' in text.lower():
                    log(f"  - '{text}'")

            # Try to find and click Reports
            if page.query_selector('text=Reports'):
                page.click('text=Reports', timeout=10000)
            elif page.query_selector('[aria-label*="Reports"]'):
                page.click('[aria-label*="Reports"]', timeout=10000)
            elif page.query_selector('button:has-text("Reports")'):
                page.click('button:has-text("Reports")', timeout=10000)
            else:
                log("ERROR: Could not find Reports menu")
                return None

            time.sleep(3)

            # Take screenshot to debug Reports menu
            screenshots_dir = Path(__file__).parent / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)
            page.screenshot(path=str(screenshots_dir / "reports_menu.png"))
            log(f"Screenshot saved: reports_menu.png")

            # Log all links on page for debugging
            links = page.query_selector_all('a')
            log(f"Found {len(links)} links on page")
            log("All link texts:")
            for i, link in enumerate(links[:30]):  # First 30 links
                text = link.inner_text().strip()
                if text:  # Only log non-empty text
                    log(f"  [{i}] '{text}'")

            # Scroll down to find Transaction Log (it's further down the list)
            log("Scrolling to find Transaction Log...")
            page.evaluate("window.scrollBy(0, 500)")  # Scroll page down
            time.sleep(2)

            # Take another screenshot after scrolling
            page.screenshot(path=str(screenshots_dir / "reports_menu_scrolled.png"))
            log(f"Screenshot saved: reports_menu_scrolled.png")

            # Try multiple case-insensitive variations
            transaction_log_found = False
            for selector in [
                'text=/transaction log/i',  # Case insensitive regex
                'text=/transaction logs/i',
                'a:has-text("Transaction")',  # Partial match
                '[href*="transaction"]',  # URL contains transaction
                '[href*="Transaction"]',
            ]:
                if page.query_selector(selector):
                    log(f"Found Transaction Log with selector: {selector}")
                    page.click(selector)
                    transaction_log_found = True
                    break

            if not transaction_log_found:
                log("ERROR: Could not find Transaction Log link")
                return None

            page.wait_for_load_state("networkidle")
            time.sleep(3)

            log("Setting date range to Year to Date...")

            # Look for date range selector - try multiple possible selectors
            # Could be a dropdown, button group, or custom date picker
            try:
                # Try clicking a "Year to Date" button or option
                if page.query_selector('text="Year to date"'):
                    page.click('text="Year to date"')
                elif page.query_selector('text="Year to Date"'):
                    page.click('text="Year to Date"')
                elif page.query_selector('button:has-text("YTD")'):
                    page.click('button:has-text("YTD")')
                else:
                    log("Could not find Year to Date selector - using default range")

                time.sleep(2)
            except Exception as e:
                log(f"Date range selection warning: {str(e)}")

            # Setup download handler
            downloads_dir = Path(__file__).parent / "downloads"
            downloads_dir.mkdir(exist_ok=True)

            log("Triggering Excel export...")

            # Start waiting for download before clicking
            with page.expect_download(timeout=60000) as download_info:
                # Try multiple export button selectors
                if page.query_selector('button:has-text("Export Excel")'):
                    page.click('button:has-text("Export Excel")')
                elif page.query_selector('button:has-text("Export")'):
                    page.click('button:has-text("Export")')
                elif page.query_selector('text="Download"'):
                    page.click('text="Download"')
                else:
                    log("ERROR: Could not find export button")
                    return None

            download = download_info.value

            # Save file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vendsoft_transaction_log_{timestamp}.xlsx"
            filepath = downloads_dir / filename
            download.save_as(filepath)

            log(f"Successfully downloaded: {filepath}")

            browser.close()
            return filepath

        except Exception as e:
            log(f"ERROR during fetch: {str(e)}")
            browser.close()
            return None

def upload_to_dashboard(filepath):
    """
    Upload the downloaded file to the dashboard endpoint
    """
    if not filepath or not filepath.exists():
        log("ERROR: File not found for upload")
        return False

    log(f"Uploading {filepath.name} to dashboard...")

    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filepath.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

            response = requests.post(
                UPLOAD_ENDPOINT,
                files=files,
                timeout=120  # 2 minute timeout for processing
            )

        if response.status_code == 200:
            result = response.json()
            log(f"✓ Upload successful!")
            log(f"  - Total transactions: {result.get('totalTransactions', 'N/A')}")
            log(f"  - New transactions: {result.get('newTransactions', 'N/A')}")
            log(f"  - Duplicates skipped: {result.get('duplicatesSkipped', 'N/A')}")
            return True
        else:
            log(f"ERROR: Upload failed with status {response.status_code}")
            log(f"Response: {response.text}")
            return False

    except Exception as e:
        log(f"ERROR during upload: {str(e)}")
        return False

def main():
    """Main courier routine"""
    log("=== Vendsoft Courier Starting ===")

    # Step 1: Fetch from Vendsoft
    filepath = fetch_transaction_log()

    if not filepath:
        log("✗ Fetch failed - aborting")
        sys.exit(1)

    # Step 2: Upload to dashboard
    success = upload_to_dashboard(filepath)

    if success:
        log("=== Sync Successful ===")
        sys.exit(0)
    else:
        log("=== Sync Failed ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
