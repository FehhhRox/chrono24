from chrono24.api import Query
import logging
import chrono24.session
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Apply FlareSolverr patch
FLARESOLVERR_URL = "http://localhost:8191/v1"
original_requests_get = requests.get


def flaresolverr_requests_get(url, **kwargs):
    """Modified requests.get that uses FlareSolverr - works with chrono24's header removal."""
    try:
        payload = {"cmd": "request.get", "url": url, "maxTimeout": 60000}
        logger.info(f"FlareSolverr request to: {url}")

        r = requests.post(FLARESOLVERR_URL, json=payload)

        if r.status_code != 200:
            logger.warning(
                f"FlareSolverr failed with status {r.status_code}, falling back to direct request"
            )
            return original_requests_get(url, **kwargs)

        response_json = r.json()
        if "solution" not in response_json:
            logger.warning(
                "FlareSolverr missing solution, falling back to direct request"
            )
            return original_requests_get(url, **kwargs)

        solution = response_json["solution"]

        # Create response object
        response = requests.Response()
        response.status_code = solution.get("status", 200)
        response._content = solution["response"].encode("utf-8")
        response.url = url
        response.headers.update(solution.get("headers", {}))

        return response

    except Exception as e:
        logger.warning(f"FlareSolverr failed: {e}, falling back to direct request")
        return original_requests_get(url, **kwargs)


# Patch only the chrono24 session module
chrono24.session.requests.get = flaresolverr_requests_get

# Test URL construction
query = Query("Audemars Piguet Royal Oak Chronograph")
query.page_size = 120

print(f"Initial self.url: {query.url}")

# Check what URL is built for page 1 using get_search_page_url
from html_fix import get_search_page_url

page1_url_fixed = get_search_page_url(query.url, page=1, page_size=query.page_size)
print(f"Page 1 URL (fixed): {page1_url_fixed}")

# Check what URL is built for page 2
page2_url = get_search_page_url(query.url, page=2, page_size=query.page_size)
print(f"Page 2 URL: {page2_url}")
