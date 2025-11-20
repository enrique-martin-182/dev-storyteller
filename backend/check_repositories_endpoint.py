import asyncio
import sys

import httpx


async def check_backend_repositories_endpoint():
    url = "http://127.0.0.1:8000/api/v1/repositories/"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            print(f"Backend response status: {response.status_code}")
            print(f"Backend response data: {response.json()}")
            return True
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}", file=sys.stderr)
    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    return False

if __name__ == "__main__":
    asyncio.run(check_backend_repositories_endpoint())
