import asyncio
import json
import re
import os
import pandas as pd
from playwright.async_api import async_playwright
from async_lru import alru_cache

class ScraperError(Exception):
    """Custom exception for scraping errors."""
    pass

@alru_cache(maxsize=32)
async def get_financial_statements_data(ticker: str) -> pd.DataFrame:
    """Fetches 10 years of financial data from a source."""
    url_template = os.getenv("DATA_SOURCE_TWO_URL")
    if not url_template:
        raise ScraperError("DATA_SOURCE_TWO_URL environment variable not set.")
    url = url_template.format(ticker=ticker)
    
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
                debug_file_path = f"debug_{ticker}.html"
                with open(debug_file_path, "w", encoding="utf-8") as f:
                    f.write(page_content)
                print(f"DEBUG: Saved page content for {ticker} to {debug_file_path}")
                # --- END DEBUGGING CODE ---
                raise ScraperError(f"Could not find or parse financial data from '{ticker}'. A debug file has been saved to the backend container.")

            df = pd.DataFrame(financial_data)
            df = df.sort_values('fiscal_year').tail(10).reset_index(drop=True)
            return df

        except Exception as e:
            print(f"An error occurred during data source 2 scraping for {ticker}: {e}")
            raise ScraperError(f"Failed to scrape data for {ticker} from data source 2.")
        finally:
            await context.close()
            await browser.close()      

@alru_cache(maxsize=32)
async  def get_key_metrics_data(ticker: str) -> dict:
    """Fetches key metrics from a source."""
    url_template = os.getenv("DATA_SOURCE_ONE_URL")
    if not url_template:
        raise ScraperError("DATA_SOURCE_ONE_URL environment variable not set.")
    url = url_template.format(ticker=ticker)
    
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
                raise ScraperError(f"Ticker '{ticker}' not found on data source 1.")

            tables = await page.query_selector_all('.snapshot-table2')
            if not tables:
                raise ScraperError(f"Could not find the data table for '{ticker}' on data source 1.")

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
                raise ScraperError(f"Extracted data is empty for '{ticker}' from data source 1.")

            return data

        except Exception as e:
            print(f"An error occurred during data source 1 scraping for {ticker}: {e}")
            raise ScraperError(f"Failed to scrape data for {ticker} from data source 1.")
        finally:
            await context.close()
            await browser.close()