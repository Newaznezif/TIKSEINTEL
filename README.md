# TIKSEINTEL - IP Threat Intelligence Aggregator

A powerful, automated threat intelligence tool that aggregates visual evidence from multiple security platforms for any given IP address.

## Features
- **Parallel Scraping**: Captures screenshots from VirusTotal, AbuseIPDB, Cisco Talos, CrowdSec, and more in parallel.
- **Visual Evidence**: Unified gallery view of actual site dashboards.
- **Auto-Cleanup**: Automatically dismisses cookie banners and popups for clean screenshots.
- **One-Click Download**: Save all evidence locally with a single button.

## Tech Stack
- **Backend**: FastAPI (Python)
- **Scraper**: Playwright (Headless Chromium)
- **Frontend**: Tailwind CSS & Vanilla JS

## Deployment
This app requires a Python environment and Playwright browser support. 
**Recommended Hosting**: [Render.com](https://render.com) (via the included `Dockerfile`).

## Local Setup
1. Install requirements: `pip install -r requirements.txt`
2. Install Playwright browsers: `playwright install chromium`
3. Run the app: `python -m uvicorn app.main:app --reload`
