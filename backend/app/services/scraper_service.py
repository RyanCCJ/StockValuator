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
                if content:
                    content = content.replace('\\"', '"')
                    if 'tableData' in content:
                        match = re.search(r'"tableData":(\[.*?\])', content)
                        if match:
                            try:
                                table_data_str = match.group(1)
                                financial_data = json.loads(table_data_str)
                                break
                            except json.JSONDecodeError:
                                continue
            
            if not financial_data:
                raise ScraperError(f"Currently unable to fetch data for non-US company ticker '{ticker}'.")

            df = pd.DataFrame(financial_data)
            df = df.sort_values('fiscal_year').tail(10).reset_index(drop=True)
            return df

        except ScraperError:
            raise
        except Exception as e:
            print(f"An error occurred during data source 2 scraping for {ticker}: {e}")
            raise ScraperError(f"Failed to scrape data for {ticker} from data source 2.")
        finally:
            await context.close()
            await browser.close()

@alru_cache(maxsize=32)
async def get_key_metrics_data(ticker: str) -> dict:
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

@alru_cache(maxsize=32)
async def get_etf_holdings_data(ticker: str) -> list:
    """Fetches top 10 ETF holdings from a source."""
    url_template = os.getenv("DATA_SOURCE_THREE_URL")
    if not url_template:
        raise ScraperError("DATA_SOURCE_THREE_URL environment variable not set.")
    url = url_template.format(ticker=ticker)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)

            # Try to find and click any common cookie consent buttons
            consent_selectors = [
                'button:has-text("Accept")',
                'button:has-text("Agree")',
                'button:has-text("I Understand")'
            ]
            for selector in consent_selectors:
                try:
                    await page.click(selector, timeout=3000) # Short timeout
                    print(f"Clicked consent button with selector: {selector}")
                    break # Exit loop once a button is clicked
                except Exception:
                    pass # Ignore if selector is not found

            # Wait for the first data row to be rendered by JavaScript.
            await page.wait_for_selector('tr[data-index="0"]', timeout=20000)
            rows = await page.query_selector_all('#etf-holdings tbody tr')
            
            holdings = []
            for row in rows[:15]: # Limit to top 15
                symbol_cell = await row.query_selector('td[data-th="Symbol"]')
                holding_cell = await row.query_selector('td[data-th="Holding"]')
                weight_cell = await row.query_selector('td[data-th="% Assets"]')
                
                if symbol_cell and holding_cell and weight_cell:
                    symbol = await symbol_cell.text_content()
                    name = await holding_cell.text_content()
                    weight = await weight_cell.text_content()
                    holdings.append({
                        'symbol': symbol.strip() if symbol else None,
                        'name': name.strip() if name else None,
                        'weight': weight.strip() if weight else None,
                    })
            
            if not holdings:
                raise ScraperError(f"Could not extract holdings for '{ticker}'.")

            return holdings

        except Exception as e:
            print(f"An error occurred during data source 3 scraping for {ticker}: {e}")
            raise ScraperError(f"Failed to scrape data for {ticker} from data source 3.")
        finally:
            await context.close()
            await browser.close()
