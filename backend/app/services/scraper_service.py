import asyncio
import json
import re
import pandas as pd
from playwright.async_api import async_playwright
from async_lru import alru_cache

class ScraperError(Exception):
    """Custom exception for scraping errors."""
    pass

@alru_cache(maxsize=32)
async def get_roic_data(ticker: str) -> pd.DataFrame:
    """
    Scrapes 10 years of financial data from roic.ai for a given ticker.
    Uses async playwright to handle dynamic JavaScript-loaded content.
    Caches results to avoid repeated scraping.
    """
    #url = f"https://roic.ai/company/{ticker}"
    url = f"https://roic.ai/quote/{ticker}/ratios?period=annual"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            script_tags = await page.query_selector_all('script')
            financial_data = None
            
            for script in script_tags:
                content = await script.text_content()
                content = content.replace('\\"', '"')
                if content and 'tableData' in content:
                    match = re.search(r'"tableData":(\[.*?\])', content)
                    if match:
                        try:
                            table_data_str = match.group(1)
                            financial_data = json.loads(table_data_str)
                            break
                        except json.JSONDecodeError:
                            continue
            
            if not financial_data:
                # --- START DEBUGGING CODE ---
                page_content = await page.content()
                debug_file_path = f"roic_debug_{ticker}.html"
                with open(debug_file_path, "w", encoding="utf-8") as f:
                    f.write(page_content)
                print(f"DEBUG: Saved page content for {ticker} to {debug_file_path}")
                # --- END DEBUGGING CODE ---
                raise ScraperError(f"Could not find or parse financial data for '{ticker}' on roic.ai. A debug file has been saved to the backend container.")

            df = pd.DataFrame(financial_data)
            df = df.sort_values('fiscal_year').tail(10).reset_index(drop=True)
            return df

        except Exception as e:
            print(f"An error occurred during scraping roic.ai for {ticker}: {e}")
            raise ScraperError(f"Failed to scrape data for {ticker} from roic.ai.")
        finally:
            await context.close()
            await browser.close()


@alru_cache(maxsize=32)
async def get_finviz_data(ticker: str) -> dict:
    """
    Scrapes the main financial table from Finviz for a given ticker.
    Uses async playwright for non-blocking web access.
    Caches results to avoid repeated scraping.
    """
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
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
            await context.close()
            await browser.close()