# Vendsoft Automated Courier

This automated courier logs into Vendsoft daily, downloads the Year-to-Date transaction log, and uploads it to your dashboard automatically.

## How It Works

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   GitHub    │       │   Vendsoft   │       │  Dashboard  │
│   Action    │──────▶│  (Download)  │──────▶│  (Upload)   │
│  (4:00 AM)  │       │     YTD      │       │   API       │
└─────────────┘       └──────────────┘       └─────────────┘
```

**Daily Routine:**
1. GitHub Action triggers at 4:00 AM UTC
2. Script logs into Vendsoft using credentials
3. Navigates to Reports > Transaction Log
4. Sets date range to "Year to Date"
5. Downloads the Excel file
6. POSTs file to `/api/upload` endpoint
7. Dashboard processes file (deduplication + mapping)

## Setup Instructions

### 1. Local Development Setup

Update your `.env.local` file with your Vendsoft credentials:

```bash
VENDSOFT_USER=your_email@vendsoft.com
VENDSOFT_PASS=your_actual_password
```

Install Python dependencies:

```bash
cd dashboard/scripts
pip install -r requirements.txt
playwright install chromium
```

### 2. Test Locally

Run the courier script manually to verify it works:

```bash
cd dashboard
python scripts/vendsoft_courier.py
```

You should see logs like:
```
[2026-02-14 04:00:00] Starting Vendsoft login...
[2026-02-14 04:00:03] Login successful!
[2026-02-14 04:00:10] Successfully downloaded: vendsoft_transaction_log_20260214_040010.xlsx
[2026-02-14 04:00:25] ✓ Upload successful!
[2026-02-14 04:00:25] === Sync Successful ===
```

### 3. GitHub Secrets Setup

For the automated daily sync to work, add your credentials to GitHub:

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these two secrets:

   **Secret 1:**
   - Name: `VENDSOFT_USER`
   - Value: `your_email@vendsoft.com`

   **Secret 2:**
   - Name: `VENDSOFT_PASS`
   - Value: `your_actual_password`

### 4. Enable GitHub Action

The workflow file `.github/workflows/sync-vendsoft.yml` is already configured to run daily at 4:00 AM UTC.

**To trigger manually:**
1. Go to **Actions** tab in GitHub
2. Click **Daily Vendsoft Sync**
3. Click **Run workflow**

### 5. Monitor Sync Status

Check the **Actions** tab to see sync history:
- ✓ Green checkmark = Successful sync
- ✗ Red X = Failed (check logs for error details)

## Customization

### Change Sync Time

Edit `.github/workflows/sync-vendsoft.yml`:

```yaml
schedule:
  # Run at 6:00 AM UTC instead of 4:00 AM
  - cron: '0 6 * * *'
```

Cron syntax: `'minute hour day month weekday'`
- `'0 4 * * *'` = 4:00 AM daily
- `'0 */6 * * *'` = Every 6 hours
- `'0 0 * * 1'` = Midnight every Monday

### Update Vendsoft Selectors

If Vendsoft's UI changes, you may need to update the selectors in `vendsoft_courier.py`:

```python
# Example: Update date range selector
page.select_option('select[name="dateRange"]', 'ytd')

# Or click buttons by text
page.click('button:has-text("Export")')
```

Use browser developer tools to inspect the correct selectors.

## Troubleshooting

**Login Failed**
- Verify credentials in GitHub Secrets
- Check if Vendsoft requires 2FA (may need API key instead)

**Download Failed**
- Verify date range selector matches Vendsoft UI
- Check if report name changed

**Upload Failed**
- Verify dashboard endpoint is accessible
- Check Vercel logs for processing errors

**Manual Sync**
Run locally with verbose output:
```bash
python scripts/vendsoft_courier.py
```

## Security Notes

- Never commit `.env.local` to Git (already in `.gitignore`)
- GitHub Secrets are encrypted and only accessible to workflows
- Credentials are never logged or exposed in console output
- Downloaded files are stored temporarily in `scripts/downloads/` (gitignored)

## File Structure

```
dashboard/
├── scripts/
│   ├── vendsoft_courier.py       # Main automation script
│   ├── requirements.txt           # Python dependencies
│   ├── README.md                  # This file
│   └── downloads/                 # Temp download storage (gitignored)
└── .env.local                     # Local credentials (gitignored)

.github/
└── workflows/
    └── sync-vendsoft.yml          # GitHub Action workflow
```
