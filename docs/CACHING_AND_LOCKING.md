# Caching & Distributed Locking

## Caching Strategy (Redis)

StockValuator uses **Redis** as a high-performance caching layer to minimize latency and reduce load on external data providers.

### Usage Patterns

1.  **API Response Caching**:
    - Frequently accessed data (e.g., Stock Prices, Financial Statements) is cached.
    - **Key Format**: `financial_data:{SYMBOL}`
    - **TTL**: Configurable (default: 24 hours for fundamentals, shorter for prices).

2.  **Code Structure**:
    - Located in `src/core/cache.py`.
    - `cache_get(key)`: Returns deserialized JSON or None.
    - `cache_set(key, value, ttl)`: Serializes and stores data.

## Distributed Locking

### The Problem: Thundering Herd on Scrapers
When a popular stock (e.g., "AAPL") is analyzed by multiple users simultaneously, and the data is not in the cache, multiple requests might try to trigger the *same* expensive scraping operation.

This leads to:
- Redundant external API calls/scrapes.
- Waste of Browser Pool resources.
- Rate limiting by external providers.

### The Solution: Redis-based Locks
We use Redis atomic operations (`SET NX`) to implement a distributed lock mechanism.

### Workflow
1.  **Request Arrives**: User asks for data for "AAPL".
2.  **Check Cache**: If data exists, return immediately.
3.  **Acquire Lock**: Try to set `lock:scrape:AAPL`.
    - **If Successful**: This process becomes the "worker". It performs the scrape, saves to DB/Cache, and releases the lock.
    - **If Failed (Locked)**: Another process is already working on this. The request waits (polls) or returns a "processing" status to the client.

### Implementation
The locking logic is encapsulated in `src/core/cache.py`:

```python
async def acquire_scrape_lock(symbol: str, ttl: int = 60) -> bool:
    """
    Returns True if lock acquired.
    Uses Redis 'SET ... NX EX ...' for atomicity.
    """
    key = f"lock:scrape:{symbol.upper()}"
    return await redis.set(key, "1", nx=True, ex=ttl)
```

### Client-Side Handling
The frontend handles this via a polling mechanism:
1.  POST `/api/analysis/{symbol}/prefetch` triggers the background task.
2.  If the backend returns `status: "fetching"`, the frontend shows a loading spinner.
3.  The frontend polls `/api/analysis/{symbol}/status` until `cached: true`.

## Implementation Guidelines (for Developers & AI Assistants)

- **Always Lock Expensive Ops**: Any operation taking > 1s involving external I/O (scraping, heavy API calls) should be protected by a unique distributed lock key (e.g., `lock:scrape:{symbol}`).
- **Set Appropriate TTLs**: Always define a Time-To-Live on locks to prevent deadlocks in case of process failure.
- **Atomic Operations**: Prefer Redis atomic commands (via our `cache.py` utilities) over read-then-write patterns to avoid race conditions.
