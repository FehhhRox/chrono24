from html_fix import get_search_page_html
from chrono24.api import Query, Listings, StandardListing
from bs4 import BeautifulSoup
import json

page = 1
while True:
    page_html = get_search_page_html(
        "Audemars Piguet Royal Oak Chronograph", page=page, page_size=120, sortorder=5
    )
    page_html = BeautifulSoup(page_html, "html.parser")

    listings = Listings(html=page_html)

    listing_id = 0
    for listing_html in listings.htmls:
        listing_json = StandardListing(listing_html).json
        with open(
            f"json_results/listing_{page}_{listing_id}.json", "w", encoding="utf-8"
        ) as f:
            json.dump(listing_json, f, ensure_ascii=False, indent=2)
        listing_id += 1
    page += 1
