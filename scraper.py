from html_fix import get_search_page_html
from chrono24.api import Query, Listings, StandardListing
from bs4 import BeautifulSoup
import json
import requests
import logging
import os
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create output directory if it doesn't exist
os.makedirs("json_results", exist_ok=True)

FLARESOLVERR_URL = "http://localhost:8191/v1"

# Store the original requests.get function
original_requests_get = requests.get


# Instead of monkeypatching globally, let's patch only the session module
# The chrono24 library already has FlareSolverr support built-in
import chrono24.session


def flaresolverr_requests_get(url, **kwargs):
    """Modified requests.get that uses FlareSolverr - works with chrono24's header removal."""
    try:
        # The chrono24 session module already removes headers, so we just need to
        # route through FlareSolverr
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

limit = 100
query_text = "Rolex DateJust"
filters = ["belgium", "new_unworn"]

try:
    i = 1
    all_listings = []  # Store all listings in memory
    logger.info("Starting scraping process...")

    query = Query(query_text, filters=filters)
    query.page_size = 120  # Both search and category formats support 120
    logger.info(f"Using page size: {query.page_size}")

    for listing in query.search(limit=limit):
        logger.info(f"Processing listing {i}" + f"/{limit}" if limit else "")

        # Add listing to our collection
        all_listings.append(listing)

        i += 1

        # # Add a small delay between requests to be respectful
        # time.sleep(0.1)

    # Save all listings to one big JSON file
    filters_str = "_".join(filters)
    output_file = f"json_results/{query_text.replace(' ', '_')}_{filters_str}.json"
    logger.info(f"Saving {len(all_listings)} listings to {output_file}")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_listings, f, ensure_ascii=False, indent=2)
        logger.info(
            f"Successfully saved all {len(all_listings)} listings to {output_file}"
        )
    except Exception as save_error:
        logger.error(f"Failed to save listings to file: {save_error}")

    logger.info(f"Successfully processed {i-1} listings")
except Exception as e:
    logger.error(f"Error during scraping: {e}")
    logger.info(
        "Try running the script again or check if FlareSolverr is running properly"
    )
