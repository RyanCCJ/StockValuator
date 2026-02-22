# Browser Pool & Memory Management

## The Problem
StockValuator relies on web scraping for certain financial metrics that are not available via standard APIs. We use **Playwright** for accurate rendering of dynamic content. However, headless browsers (Chromium) are resource-intensive:
1.  **Memory Leaks**: Long-running browser processes often accumulate memory.
2.  **Startup Latency**: Launching a new browser for every request adds significant overhead (1-2 seconds).
3.  **Concurrency Limits**: Running too many browsers simultaneously can crash the host server.

## The Solution: Managed Browser Pool

We implemented a custom `BrowserPool` class (`src/core/browser_pool.py`) to manage Playwright instances efficiently.

### Key Features

1.  **Instance Reuse**: 
    Browsers are kept alive and reused across requests. Instead of launching a browser, we create a lightweight `BrowserContext` for each scraping job. This isolates cookies/sessions but shares the heavy browser process.

2.  **Lifecycle Management (Recycling)**:
    To prevent memory leaks, each browser instance tracks its usage count.
    - **`max_usage_per_browser`**: After serving N requests (default: 100), the browser is gracefully closed and replaced with a fresh instance.
    - **Health Checks**: If a browser crashes or becomes unresponsive, it is marked unhealthy and removed from the pool.

3.  **Concurrency Control**:
    - **`max_browsers`**: Limits the total number of heavyweight browser processes (default: 3).
    - **`asyncio.Semaphore`**: Queues incoming requests if all browsers are busy. This prevents server overload during traffic spikes.

### Implementation Details

```python
# Simplified Logic
async def acquire(self):
    # 1. Wait for available slot
    await self.semaphore.acquire()
    
    # 2. Get or Create Browser
    if browser.usage_count > MAX_USAGE:
        await browser.close()
        browser = await create_new_browser()
        
    # 3. Create isolated context
    context = await browser.new_context()
    return browser, context
```

### Configuration
The pool behavior is controlled via environment variables in `.env`:
- `MAX_BROWSERS`: Number of concurrent chromium instances.
- `BROWSER_TIMEOUT`: Max time to wait for a browser slot.

## Implementation Guidelines (for Developers & AI Assistants)

When extending the scraping logic or adding new scrapers, follow these rules to ensure system stability:

- **Always use the pool**: Never launch `async_playwright()` directly in route handlers or services. Use `BrowserContextManager` to acquire an instance.
- **Context Management**: Ensure every `BrowserContext` is closed and the semaphore is released (the context manager handles this automatically).
- **Resource Awareness**: Scrapers must be designed to be fast and lightweight. Minimize the time spent holding a browser slot to prevent pool exhaustion.
- **User-Agent Consistency**: Use the default User-Agent provided by the pool to avoid detection and maintain consistency across requests.
