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
            page.goto(VENDSOFT_URL, timeout=30000)

            # Wait for login page to load
            page.wait_for_load_state("networkidle")

            # Fill in login credentials
            log("Entering credentials...")
            page.fill('input[name="email"]', VENDSOFT_USER)
            page.fill('input[name="password"]', VENDSOFT_PASS)

            # Click login button
            log("Clicking login button...")
            page.click('button[type="submit"]')

            # Wait for dashboard to load
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            # Check if login was successful
            if "login" in page.url.lower():
                log("ERROR: Login failed - still on login page")
                return None

            log("Login successful!")

            # Navigate to Reports > Transaction Log
            log("Navigating to Transaction Log report...")

            # Click on Reports menu
            page.click('text=Reports')
            time.sleep(1)

            # Click on Transaction Log
            page.click('text=Transaction Log')
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            log("Setting date range to Year to Date...")

            # Select "Year to Date" date range
            # Note: You may need to adjust these selectors based on actual Vendsoft UI
            page.click('select[name="dateRange"]')
            page.select_option('select[name="dateRange"]', 'ytd')
            time.sleep(1)

            # Setup download handler
            downloads_dir = Path(__file__).parent / "downloads"
            downloads_dir.mkdir(exist_ok=True)

            log("Triggering Excel export...")

            # Start waiting for download before clicking
            with page.expect_download() as download_info:
                # Click export/download button
                page.click('button:has-text("Export")')
                # or page.click('text=Download Excel')

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
