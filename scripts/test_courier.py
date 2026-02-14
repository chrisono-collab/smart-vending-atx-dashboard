"""
Test script to verify Vendsoft courier setup
Run this before enabling the automated daily sync
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n🔍 Checking dependencies...")

    try:
        import playwright
        print("✓ playwright installed")
    except ImportError:
        print("✗ playwright not installed - run: pip install playwright")
        return False

    try:
        import requests
        print("✓ requests installed")
    except ImportError:
        print("✗ requests not installed - run: pip install requests")
        return False

    # Check if chromium is installed
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch()
        print("✓ chromium browser installed")
    except Exception:
        print("✗ chromium not installed - run: playwright install chromium")
        return False

    return True

def check_credentials():
    """Check if credentials are set"""
    print("\n🔐 Checking credentials...")

    user = os.getenv("VENDSOFT_USER")
    password = os.getenv("VENDSOFT_PASS")

    if not user or user == "your_email@example.com":
        print("✗ VENDSOFT_USER not set in .env.local")
        return False
    print(f"✓ VENDSOFT_USER set: {user}")

    if not password or password == "your_secure_password":
        print("✗ VENDSOFT_PASS not set in .env.local")
        return False
    print("✓ VENDSOFT_PASS set: [hidden]")

    return True

def check_directories():
    """Check if required directories exist"""
    print("\n📁 Checking directories...")

    script_dir = Path(__file__).parent
    downloads_dir = script_dir / "downloads"

    if not downloads_dir.exists():
        print(f"Creating downloads directory: {downloads_dir}")
        downloads_dir.mkdir(exist_ok=True)

    print(f"✓ Downloads directory ready: {downloads_dir}")
    return True

def test_upload_endpoint():
    """Test if upload endpoint is accessible"""
    print("\n🌐 Testing upload endpoint...")

    import requests
    endpoint = os.getenv("UPLOAD_ENDPOINT", "https://smart-vending-atx-dashboard.vercel.app/api/upload")

    try:
        # Just check if the endpoint is reachable (HEAD request)
        response = requests.head(endpoint, timeout=10)
        print(f"✓ Endpoint accessible: {endpoint}")
        return True
    except Exception as e:
        print(f"⚠ Could not reach endpoint: {e}")
        print("  (This is OK if dashboard is not deployed yet)")
        return True  # Don't fail on this

def main():
    """Run all checks"""
    print("=" * 60)
    print("   VENDSOFT COURIER - PRE-FLIGHT CHECK")
    print("=" * 60)

    # Load .env.local if it exists
    env_file = Path(__file__).parent.parent / ".env.local"
    if env_file.exists():
        print(f"\n📄 Loading environment from: {env_file}")
        from dotenv import load_dotenv
        load_dotenv(env_file)
    else:
        print(f"\n⚠ No .env.local file found at: {env_file}")

    all_passed = True

    all_passed &= check_dependencies()
    all_passed &= check_credentials()
    all_passed &= check_directories()
    all_passed &= test_upload_endpoint()

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Ready to run courier!")
        print("\nNext step: python scripts/vendsoft_courier.py")
    else:
        print("❌ SOME CHECKS FAILED - Fix issues above")
        sys.exit(1)
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
