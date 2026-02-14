"""
Inspect Vendsoft UI to identify correct selectors
Opens Vendsoft with a visible browser window so you can see the page structure
"""

import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import time
from dotenv import load_dotenv

# Load environment
env_file = Path(__file__).parent.parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)

VENDSOFT_URL = "https://www.vendsoft.com/"
VENDSOFT_USER = os.getenv("VENDSOFT_USER")
VENDSOFT_PASS = os.getenv("VENDSOFT_PASS")

def inspect_vendsoft():
    """Open Vendsoft in a visible browser for manual inspection"""
    print("\n" + "="*60)
    print("  VENDSOFT UI INSPECTOR")
    print("="*60)
    print("\nOpening Vendsoft in browser window...")
    print("Instructions:")
    print("1. Browser will open to Vendsoft login page")
    print("2. Script will attempt auto-login")
    print("3. Right-click elements and select 'Inspect'")
    print("4. Check the actual field names, button IDs, etc.")
    print("5. Press Ctrl+C in terminal when done")
    print("\n" + "="*60 + "\n")

    with sync_playwright() as p:
        # Launch browser in VISIBLE mode (headless=False)
        browser = p.chromium.launch(
            headless=False,  # Show browser window
            slow_mo=1000     # Slow down actions for visibility
        )

        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to Vendsoft
            print(f"✓ Navigating to {VENDSOFT_URL}")
            page.goto(VENDSOFT_URL, timeout=30000)
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            # Take screenshot of login page
            screenshots_dir = Path(__file__).parent / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)
            page.screenshot(path=str(screenshots_dir / "01_login_page.png"))
            print(f"✓ Screenshot saved: screenshots/01_login_page.png")

            # Try to find login fields
            print("\n📋 Inspecting login page elements...")

            # Try common username selectors
            username_selectors = [
                'input[name="username"]',
                'input[name="email"]',
                'input[type="email"]',
                'input[id="username"]',
                'input[id="email"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="username" i]',
            ]

            username_found = None
            for selector in username_selectors:
                if page.query_selector(selector):
                    username_found = selector
                    print(f"  ✓ Username field found: {selector}")
                    break

            if not username_found:
                print("  ✗ Username field not found with common selectors")
                print("    → Right-click the email/username field and inspect it")

            # Try common password selectors
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[id="password"]',
            ]

            password_found = None
            for selector in password_selectors:
                if page.query_selector(selector):
                    password_found = selector
                    print(f"  ✓ Password field found: {selector}")
                    break

            if not password_found:
                print("  ✗ Password field not found with common selectors")
                print("    → Right-click the password field and inspect it")

            # Try common submit button selectors
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Sign in")',
                'button:has-text("Login")',
            ]

            submit_found = None
            for selector in submit_selectors:
                if page.query_selector(selector):
                    submit_found = selector
                    print(f"  ✓ Submit button found: {selector}")
                    break

            if not submit_found:
                print("  ✗ Submit button not found with common selectors")
                print("    → Right-click the login button and inspect it")

            # Attempt login if credentials provided and fields found
            if username_found and password_found and submit_found:
                print("\n🔐 Attempting auto-login...")
                page.fill(username_found, VENDSOFT_USER)
                page.fill(password_found, VENDSOFT_PASS)
                page.click(submit_found)

                page.wait_for_load_state("networkidle")
                time.sleep(3)

                # Take screenshot after login
                page.screenshot(path=str(screenshots_dir / "02_after_login.png"))
                print(f"✓ Screenshot saved: screenshots/02_after_login.png")

                if "login" in page.url.lower():
                    print("⚠ Still on login page - check credentials or 2FA requirement")
                else:
                    print("✓ Login appears successful!")

                    # Try to find Reports menu
                    print("\n📋 Looking for Reports menu...")
                    reports_selectors = [
                        'text=Reports',
                        'a:has-text("Reports")',
                        'button:has-text("Reports")',
                        '[href*="reports" i]',
                    ]

                    for selector in reports_selectors:
                        if page.query_selector(selector):
                            print(f"  ✓ Reports menu found: {selector}")
                            break
                    else:
                        print("  ✗ Reports menu not found")
                        print("    → Inspect the navigation menu for the correct selector")

            print("\n" + "="*60)
            print("✓ Browser window is open for inspection")
            print("  - Use browser DevTools (right-click → Inspect)")
            print("  - Check screenshots in scripts/screenshots/")
            print("  - Press Ctrl+C in terminal when done")
            print("="*60 + "\n")

            # Keep browser open for manual inspection
            input("Press Enter to close browser...")

        except KeyboardInterrupt:
            print("\n✓ Closing browser...")
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")
        finally:
            browser.close()

if __name__ == "__main__":
    inspect_vendsoft()
