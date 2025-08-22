import asyncio
from playwright.async_api import async_playwright
from functools import lru_cache

class ScraperError(Exception):
    """Custom exception for scraping errors."""
    pass

@lru_cache(maxsize=32)
async def get_finviz_data(ticker: str) -> dict:
    """
    Scrapes the main financial table from Finviz for a given ticker.
    Uses async playwright for non-blocking web access.
    Caches results to avoid repeated scraping.
    """
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Set a realistic User-Agent to avoid being blocked
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            # Increased timeout for robustness
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Check if the page is valid (e.g., "Stock not found")
            not_found_element = await page.query_selector('td.body-text b:has-text("Stock not found!")')
            if not_found_element:
                raise ScraperError(f"Ticker '{ticker}' not found on Finviz.")

            tables = await page.query_selector_all('.snapshot-table2')
            if not tables:
                raise ScraperError(f"Could not find the data table for '{ticker}' on Finviz.")

            data = {}
            rows = await tables[0].query_selector_all('tr')
            
            for row in rows:
                cols = await row.query_selector_all('td')
                if len(cols) % 2 != 0:
                    continue

                for i in range(0, len(cols), 2):
                    key = (await cols[i].text_content() or "").strip()
                    value = (await cols[i+1].text_content() or "").strip()
                    if key:
                        data[key] = value
            
            if not data:
                raise ScraperError(f"Extracted data is empty for '{ticker}' from Finviz.")

            return data

        except Exception as e:
            print(f"An error occurred during scraping Finviz for {ticker}: {e}")
            raise ScraperError(f"Failed to scrape data for {ticker} from Finviz.")
        finally:
            # Ensure context is closed as well
            await context.close()
            await browser.close()