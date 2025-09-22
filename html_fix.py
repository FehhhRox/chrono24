import requests
from urllib.parse import urljoin, quote_plus
from bs4 import BeautifulSoup

FLARE_URL = "http://localhost:8191/v1"  # or your WSL2 IP

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def _safe_urljoin_preserve_search(base_url, href_url, original_page1_url):
    """
    Helper function to urljoin while preserving /search/ structure when needed.

    Args:
        base_url: Base URL like "https://www.chrono24.com"
        href_url: The href to join (could be relative or absolute)
        original_page1_url: The original page 1 URL to check for search format

    Returns:
        The properly constructed URL maintaining /search/ structure if needed
    """
    # If the original URL uses search format and the href is a relative path to index.htm,
    # redirect it to /search/index.htm to maintain the search format
    if "/search/index.htm" in original_page1_url:
        if (
            str(href_url).startswith("/")
            and "index.htm" in str(href_url)
            and not str(href_url).startswith("/search/")
        ):
            href_str = str(href_url)
            if href_str.startswith("/index.htm"):
                href_url = href_str.replace("/index.htm", "/search/index.htm", 1)

    return urljoin(base_url, str(href_url))


def flaresolverr_get_html(url: str, headers: dict | None = None) -> str:
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000,
    }
    # Note: FlareSolverr v2 doesn't support headers, so we exclude them
    # if headers:
    #     payload["headers"] = headers
    r = requests.post(FLARE_URL, json=payload)
    r.raise_for_status()
    return r.json()["solution"]["response"]


def build_search_page1_url(query: str, page_size: int = 120, sortorder: int = 5) -> str:
    q = quote_plus(query)
    return f"https://www.chrono24.com/search/index.htm?dosearch=true&query={q}&sortorder={sortorder}&pageSize={page_size}"


# Cache for URL patterns discovered for different queries
_url_pattern_cache = {}


def get_search_page_url(
    page1_url, page: int = 1, page_size: int = 120, sortorder: int = 5
) -> str:
    # Check if this is a search URL format - if so, use showpage= pagination directly
    if "/search/index.htm" in page1_url:
        # This is a search URL - it will stay in search format and use showpage= pagination
        if page == 1:
            # Ensure page 1 has the correct page size parameter
            if f"pageSize={page_size}" not in page1_url:
                separator = "&" if "?" in page1_url else "?"
                page1_url += f"{separator}pageSize={page_size}"
            return page1_url
        else:
            # For page > 1, add showpage parameter
            if f"pageSize={page_size}" not in page1_url:
                separator = "&" if "?" in page1_url else "?"
                page1_url += f"{separator}pageSize={page_size}"

            # Add or update showpage parameter
            if "showpage=" in page1_url:
                # Replace existing showpage
                import re

                page1_url = re.sub(r"showpage=\d+", f"showpage={page}", page1_url)
            else:
                page1_url += f"&showpage={page}"

            return page1_url

    # Original logic for non-filtered queries that redirect to category format
    # Always discover the category URL format from the search results
    # as the search URL format has limitations (only 60 listings per page)
    html = flaresolverr_get_html(page1_url, headers=DEFAULT_HEADERS)

    # Check if we have a cached URL pattern for this query
    cache_key = (page1_url, page_size, sortorder)
    if cache_key in _url_pattern_cache:
        url_pattern, pattern_type = _url_pattern_cache[cache_key]
        if pattern_type == "showpage":
            # The cached pattern is for page 2, derive page 1
            if page == 1:
                target_url = url_pattern.replace(f"showPage=2", f"showPage=1")
            else:
                target_url = url_pattern.replace(f"showPage=2", f"showPage={page}")
        elif pattern_type == "index":
            if page == 1:
                target_url = url_pattern.replace(f"index-2.htm", f"index.htm")
            else:
                target_url = url_pattern.replace(f"index-2.htm", f"index-{page}.htm")
        elif pattern_type == "next":
            # For "next" pattern, we need to iteratively follow links
            if page == 1:
                return url_pattern
            # Follow next links iteratively
            cur_url = url_pattern
            for cur in range(2, page + 1):
                cur_html = flaresolverr_get_html(cur_url, headers=DEFAULT_HEADERS)
                soup = BeautifulSoup(cur_html, "html.parser")
                rel_next = soup.find("link", rel="next")
                if not rel_next:
                    raise RuntimeError(
                        "Could not find further pagination (rel='next' missing)."
                    )
                try:
                    next_href = rel_next.attrs["href"]  # type: ignore
                except (KeyError, AttributeError):
                    raise RuntimeError(
                        "Could not find further pagination (rel='next' missing)."
                    )
                cur_url = _safe_urljoin_preserve_search(
                    "https://www.chrono24.com", next_href, page1_url
                )
            return cur_url
        else:  # pattern_type == "page"
            if page == 1:
                target_url = url_pattern.replace(f"-2.htm", f".htm")
            else:
                target_url = url_pattern.replace(f"-2.htm", f"-{page}.htm")

        return target_url

    # First time for this query - need to discover the URL pattern from page 1
    soup = BeautifulSoup(html, "html.parser")

    # Strategy A: find an <a> whose href contains showpage=2 or ends with -2.htm or whose text == "2"
    candidate_href = None
    pattern_type = None
    for a in soup.find_all("a", href=True):
        try:
            href = a.attrs["href"]  # type: ignore
        except (KeyError, AttributeError):
            continue
        href = str(href)
        if "showpage=2" in href:
            candidate_href = href
            pattern_type = "showpage"
            break
        elif href.endswith("-2.htm") or "index-2.htm" in href:
            candidate_href = href
            pattern_type = "index" if "index-2.htm" in href else "page"
            break
        elif a.get_text(strip=True) == "2":
            candidate_href = href
            pattern_type = "page"
            break

    # Strategy B fallback: follow rel="next" link to get page 2
    if not candidate_href:
        rel_next = soup.find("link", rel="next")
        if rel_next:
            try:
                next_href = rel_next.attrs["href"]  # type: ignore
            except (KeyError, AttributeError):
                next_href = None
            if next_href:
                # Apply the same fix for next_href URLs to maintain search format
                next_url = _safe_urljoin_preserve_search(
                    "https://www.chrono24.com", next_href, page1_url
                )
                if page == 2:
                    # Cache this URL pattern for future use
                    _url_pattern_cache[cache_key] = (next_url, "next")
                    return next_url

                # Get page 2 to discover the pattern
                page2_html = flaresolverr_get_html(next_url, headers=DEFAULT_HEADERS)

                # Try to extract pattern from page 2 URL
                if "showpage=2" in next_url:
                    pattern_type = "showpage"
                    candidate_href = next_url
                elif "index-2.htm" in next_url or next_url.endswith("-2.htm"):
                    pattern_type = "index" if "index-2.htm" in next_url else "page"
                    candidate_href = next_url
                else:
                    # Fallback to iterative approach for this specific page
                    if page == 2:
                        return next_url
                    # Continue iteratively for higher pages
                    cur = 3
                    cur_url = next_url
                    while cur <= page:
                        cur_html = flaresolverr_get_html(
                            cur_url, headers=DEFAULT_HEADERS
                        )
                        soup2 = BeautifulSoup(cur_html, "html.parser")
                        rel_next2 = soup2.find("link", rel="next")
                        if not rel_next2:
                            raise RuntimeError(
                                "Could not find further pagination (rel='next' missing)."
                            )
                        try:
                            next_href2 = rel_next2.attrs["href"]  # type: ignore
                        except (KeyError, AttributeError):
                            raise RuntimeError(
                                "Could not find further pagination (rel='next' missing)."
                            )
                        cur_url = _safe_urljoin_preserve_search(
                            "https://www.chrono24.com", next_href2, page1_url
                        )
                        if cur == page:
                            return cur_url
                        cur += 1
        else:
            raise RuntimeError(
                "Could not find a pagination link on page 1 (no obvious showpage/-N link and no rel='next')."
            )

    if not candidate_href:
        raise RuntimeError("Could not determine URL pattern for pagination.")

    # normalize candidate href to absolute URL and add page size
    # Use helper function to preserve search format when needed
    target_url = _safe_urljoin_preserve_search(
        "https://www.chrono24.com", candidate_href, page1_url
    )

    if f"pageSize={page_size}" not in target_url:
        target_url += f"&pageSize={page_size}"

    # For the "page" pattern, derive the page 1 URL from the page 2 URL
    if pattern_type == "page":
        page1_category_url = target_url.replace("-2.htm", ".htm")
        _url_pattern_cache[cache_key] = (target_url, pattern_type)
    elif pattern_type == "index":
        page1_category_url = target_url.replace("index-2.htm", "index.htm")
        _url_pattern_cache[cache_key] = (target_url, pattern_type)
    elif pattern_type == "showpage":
        page1_category_url = target_url.replace("showPage=2", "showPage=1")
        _url_pattern_cache[cache_key] = (target_url, pattern_type)
    else:
        # Should not reach here, but fallback
        page1_category_url = target_url
        _url_pattern_cache[cache_key] = (target_url, pattern_type)

    # Generate URL for the requested page
    if page == 1:
        return page1_category_url
    elif pattern_type == "showpage":
        final_url = target_url.replace(f"showPage=2", f"showPage={page}")
    elif pattern_type == "index":
        final_url = target_url.replace(f"index-2.htm", f"index-{page}.htm")
    else:  # pattern_type == "page"
        final_url = target_url.replace(f"-2.htm", f"-{page}.htm")

    return final_url


def get_search_page_html(search_page_url):
    return flaresolverr_get_html(search_page_url, headers=DEFAULT_HEADERS)


# Example usage:
if __name__ == "__main__":
    pass
