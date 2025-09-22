#!/usr/bin/env python3

import sys

sys.path.append(".")

from chrono24.api import Query, BASE_URL
from chrono24.session import get_response

# Test the URL generation process
query_text = "Audemars Piguet Royal Oak Selfwinding"

print("=== URL Generation Debug ===")
print(f"Query: {query_text}")
print()

# Step 1: See what the initial query URL looks like
initial_url = (
    f"{BASE_URL}/search/index.htm?dosearch=true&query={query_text.replace(' ', '+')}"
)
print(f"1. Initial search URL: {initial_url}")

# Step 2: Create Query object and see what happens
query = Query(query_text)
query.page_size = 120

print(f"2. Query.url after initialization: {query.url}")
print(f"3. Filters parameters: {query.filters.parameters}")

# Step 3: Test what get_response does to the URL
print("\n=== Testing get_response behavior ===")
test_url = initial_url + "&" + query.filters.parameters
print(f"Test URL before get_response: {test_url}")

try:
    response = get_response(test_url)
    print(f"Response URL after get_response: {response.url}")
    print(f"Response status: {response.status_code}")
except Exception as e:
    print(f"Error during get_response: {e}")

print("\n=== Testing get_search_page_url function ===")
from html_fix import get_search_page_url

try:
    # Test pagination URLs
    page1_url = get_search_page_url(query.url, page=1, page_size=120)
    page2_url = get_search_page_url(query.url, page=2, page_size=120)

    print(f"Page 1 URL: {page1_url}")
    print(f"Page 2 URL: {page2_url}")
except Exception as e:
    print(f"Error during get_search_page_url: {e}")
