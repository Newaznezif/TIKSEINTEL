import asyncio
from playwright.async_api import async_playwright
import os

SCREENSHOTS_DIR = "app/static/screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

async def fetch_screenshot(context, name, url, ip):
    page = await context.new_page()
    # Speed up: Block trackers and analytics
    await page.route("**/*.{png,jpg,jpeg,gif,webp,svg}", lambda route: route.continue_()) # Allow images for screenshots
    await page.route("**/google-analytics.com/**", lambda route: route.abort())
    await page.route("**/googletagmanager.com/**", lambda route: route.abort())
    await page.route("**/doubleclick.net/**", lambda route: route.abort())
    await page.route("**/facebook.net/**", lambda route: route.abort())
    
    screenshot_path = f"{SCREENSHOTS_DIR}/{ip}_{name}.png"
    try:
        # 1. Load the page up to DOMContentLoaded (fast and reliable)
        print(f"[{name}] Navigating to {url} with timeout=25000ms")
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        
        # 2. Try to wait for network to settle (optional, don't fail if it doesn't)
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass

        # Final wait for any late-loading JS components and animations
        await page.wait_for_timeout(20000)

        # Site-specific interactions
        if name == "crowdsec":
            try:
                # Target the specific CrowdSec modal close button and quota popups
                await page.evaluate("""
                    () => {
                        const closeBtns = [
                            ...document.querySelectorAll('button[aria-label="Close"]'),
                            ...document.querySelectorAll('.modal-close'),
                            ...document.querySelectorAll('.close-button'),
                            ...document.querySelectorAll('[class*="CloseIcon"]')
                        ];
                        closeBtns.forEach(btn => btn.click());
                        
                        // Specifically hide quota warnings if clicking doesn't work
                        document.querySelectorAll('[class*="quota"], [id*="quota"]').forEach(el => el.style.display = 'none');
                    }
                """)
                await page.wait_for_timeout(2000)
            except: pass
            
        elif name == "criminalip":
            try:
                # Criminal IP sometimes needs an explicit search to show the right dashboard
                search_input = await page.wait_for_selector('input[id*="search"], input[placeholder*="IP"]', timeout=5000)
                if search_input:
                    await search_input.fill("") # Clear first
                    await search_input.fill(ip)
                    await search_input.press("Enter")
                    # Wait for the results dashboard to definitely appear
                    await page.wait_for_selector('.asset-detail, .ip-detail', timeout=15000)
                    await page.wait_for_timeout(3000)
            except: pass

        elif name == "talos":
            try:
                # Cisco Talos: if results aren't visible, search again
                if not await page.query_selector('.reputation-data'):
                    search_input = await page.wait_for_selector('#search-input, input[name="search"]', timeout=5000)
                    if search_input:
                        await search_input.fill(ip)
                        await search_input.press("Enter")
                await page.wait_for_selector('.reputation-data, #reputation-results', timeout=15000)
                await page.wait_for_timeout(5000) # Final settle
            except: pass
        
        # UI Cleanup: Hide popups, cookie banners, and modals
        await page.evaluate("""
            () => {
                const selectors = [
                    '[id*="cookie"]', '[class*="cookie"]', 
                    '[id*="consent"]', '[class*="consent"]',
                    '[class*="modal"]', '[id*="modal"]',
                    '[class*="overlay"]', '[id*="overlay"]',
                    '[class*="popup"]', '[id*="popup"]',
                    '[class*="banner"]', '[id*="banner"]',
                    '[id*="axeptio"]', '[class*="axeptio"]',
                    '.fc-consent-root', '.tp-modal', '.tp-backdrop',
                    '#CybotCookiebotDialog'
                ];
                selectors.forEach(s => {
                    document.querySelectorAll(s).forEach(el => {
                        el.style.display = 'none';
                        el.style.opacity = '0';
                        el.style.visibility = 'hidden';
                    });
                });
                // Remove blurring/dimming if any
                document.body.style.overflow = 'auto';
                document.querySelectorAll('*').forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.filter.includes('blur')) el.style.filter = 'none';
                    if (style.backdropFilter.includes('blur')) el.style.backdropFilter = 'none';
                });
            }
        """)
        await page.wait_for_timeout(1000)
        
        # Scroll down and up to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)

        await page.screenshot(path=screenshot_path, full_page=True)
        return {
            "name": name,
            "status": "success",
            "path": f"/static/screenshots/{ip}_{name}.png",
            "url": url
        }
    except Exception as e:
        print(f"Error capturing {name}: {e}")
        return {
            "name": name,
            "status": "error",
            "error": str(e),
            "url": url
        }
    finally:
        await page.close()

async def fetch_screenshot_apivoid(context, name, url, ip):
    page = await context.new_page()
    # Speed up: Block trackers and analytics
    await page.route("**/google-analytics.com/**", lambda route: route.abort())
    await page.route("**/googletagmanager.com/**", lambda route: route.abort())
    
    screenshot_path = f"{SCREENSHOTS_DIR}/{ip}_{name}.png"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        try:
            # Attempt to find the input field and submit it
            inputs = await page.query_selector_all('input[type="text"]')
            if inputs:
                await inputs[0].fill(ip)
                buttons = await page.query_selector_all('button[type="submit"], input[type="submit"], button.btn-primary')
                if buttons:
                    await buttons[0].click()
                    # Wait for results container to appear
                    try:
                        await page.wait_for_selector('.result-container, .table-responsive', timeout=15000)
                    except:
                        pass
                    await page.wait_for_timeout(10000)
        except Exception as e:
            print(f"Could not interact with APIVoid form: {e}")
            
        # UI Cleanup: Hide popups, cookie banners, and modals
        await page.evaluate("""
            () => {
                const selectors = [
                    '[id*="cookie"]', '[class*="cookie"]', 
                    '[id*="consent"]', '[class*="consent"]',
                    '[class*="modal"]', '[id*="modal"]',
                    '[class*="overlay"]', '[id*="overlay"]',
                    '[class*="popup"]', '[id*="popup"]',
                    '[class*="banner"]', '[id*="banner"]',
                    '.fc-consent-root', '.tp-modal', '.tp-backdrop',
                    '#CybotCookiebotDialog'
                ];
                selectors.forEach(s => {
                    document.querySelectorAll(s).forEach(el => {
                        el.style.display = 'none';
                        el.style.opacity = '0';
                        el.style.visibility = 'hidden';
                    });
                });
                // Remove blurring/dimming if any
                document.body.style.overflow = 'auto';
                document.querySelectorAll('*').forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.filter.includes('blur')) el.style.filter = 'none';
                    if (style.backdropFilter.includes('blur')) el.style.backdropFilter = 'none';
                });
            }
        """)
        await page.wait_for_timeout(1000)
                    
        # Scroll down and up to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)

        await page.screenshot(path=screenshot_path, full_page=True)
        return {
            "name": name,
            "status": "success",
            "path": f"/static/screenshots/{ip}_{name}.png",
            "url": url
        }
    except Exception as e:
        print(f"Error capturing {name}: {e}")
        return {
            "name": name,
            "status": "error",
            "error": str(e),
            "url": url
        }
    finally:
        await page.close()

async def gather_screenshots(ip: str):
    async with async_playwright() as p:
        # Improved stealth launch
        browser = await p.chromium.launch(
            headless=True, 
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certifcate-errors',
                '--ignore-certifcate-errors-spki-list',
            ]
        )
        
        # Create context with more human-like properties
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            has_touch=False,
            is_mobile=False,
            locale="en-US",
            timezone_id="America/New_York"
        )
        
        # Additional stealth: override navigator.webdriver
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        tasks = [
            fetch_screenshot(context, "virustotal", f"https://www.virustotal.com/gui/ip-address/{ip}", ip),
            fetch_screenshot(context, "abuseipdb", f"https://www.abuseipdb.com/check/{ip}", ip),
            fetch_screenshot(context, "mxtoolbox", f"https://mxtoolbox.com/SuperTool.aspx?action=blacklist%3a{ip}", ip),
            fetch_screenshot(context, "otx", f"https://otx.alienvault.com/indicator/ip/{ip}", ip),
            fetch_screenshot(context, "crowdsec", f"https://app.crowdsec.net/cti/{ip}", ip),
            fetch_screenshot(context, "talos", f"https://talosintelligence.com/reputation_center/lookup?search={ip}", ip),
            fetch_screenshot(context, "criminalip", f"https://www.criminalip.io/asset/ip/{ip}", ip),
            fetch_screenshot_apivoid(context, "apivoid", "https://www.apivoid.com/tools/ip-reputation-check/", ip)
        ]
        
        results = await asyncio.gather(*tasks)
        await browser.close()
        return results
