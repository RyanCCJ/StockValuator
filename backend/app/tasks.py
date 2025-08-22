import asyncio
from .celery_app import celery
from .services import scraper_service

@celery.task(name='tasks.update_finviz_data')
def update_finviz_data(ticker: str):
    """
    A Celery task to scrape data from Finviz for a given ticker.
    """
    print(f"Starting background task to scrape Finviz for {ticker}")
    
    try:
        # Since the scraper function is async, we need to run it in an event loop.
        # Celery workers are synchronous, so we manage the asyncio loop manually.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        data = loop.run_until_complete(scraper_service.get_finviz_data(ticker))
        
        # In a real application, you would save this data to the database.
        # For now, we'll just print a success message and a snippet of the data.
        print(f"Successfully scraped Finviz for {ticker}. Found {len(data)} data points.")
        print(f"Sample data for {ticker}: P/E = {data.get('P/E', 'N/A')}, ROE = {data.get('ROE', 'N/A')}")
        
        return {"status": "Success", "ticker": ticker, "data_points": len(data)}
        
    except Exception as e:
        print(f"Error during Finviz scraping task for {ticker}: {e}")
        return {"status": "Failed", "ticker": ticker, "error": str(e)}
