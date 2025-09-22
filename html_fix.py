import requests
from urllib.parse import urljoin, quote_plus
from bs4 import BeautifulSoup
import chrono24

FLARE_URL = "http://localhost:8191/v1"  # or your WSL2 IP

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def flaresolverr_get_html(url: str, headers: dict | None = None) -> str:
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000,
    }
    if headers:
        payload["headers"] = headers
    r = requests.post(FLARE_URL, json=payload)
    r.raise_for_status()
    return r.json()["solution"]["response"]


def build_search_page1_url(query: str, page_size: int = 120, sortorder: int = 5) -> str:
    q = quote_plus(query)
    return f"https://www.chrono24.com/search/index.htm?dosearch=true&query={q}&sortorder={sortorder}&pageSize={page_size}"


# Cache for URL patterns discovered for different queries
_url_pattern_cache = {}


def get_search_page_html(
    query: str, page: int = 1, page_size: int = 120, sortorder: int = 5
) -> str:
    page1_url = build_search_page1_url(query, page_size=page_size, sortorder=sortorder)
    html = flaresolverr_get_html(page1_url, headers=DEFAULT_HEADERS)
    if page == 1:
        return html

    # Check if we have a cached URL pattern for this query
    cache_key = (query, page_size, sortorder)
    if cache_key in _url_pattern_cache:
        url_pattern, pattern_type = _url_pattern_cache[cache_key]
        if pattern_type == "showpage":
            target_url = url_pattern.replace(f"showpage=2", f"showpage={page}")
        elif pattern_type == "index":
            target_url = url_pattern.replace(f"index-2.htm", f"index-{page}.htm")
        else:  # pattern_type == "page"
            target_url = url_pattern.replace(f"-2.htm", f"-{page}.htm")

        return flaresolverr_get_html(target_url, headers=DEFAULT_HEADERS)

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
                next_url = urljoin("https://www.chrono24.com", str(next_href))
                if page == 2:
                    # Cache this URL pattern for future use
                    _url_pattern_cache[cache_key] = (next_url, "next")
                    return flaresolverr_get_html(next_url, headers=DEFAULT_HEADERS)

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
                        return page2_html
                    # Continue iteratively for higher pages
                    cur = 3
                    while cur <= page:
                        soup2 = BeautifulSoup(page2_html, "html.parser")
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
                        next_url = urljoin("https://www.chrono24.com", str(next_href2))
                        page2_html = flaresolverr_get_html(
                            next_url, headers=DEFAULT_HEADERS
                        )
                        if cur == page:
                            return page2_html
                        cur += 1
        else:
            raise RuntimeError(
                "Could not find a pagination link on page 1 (no obvious showpage/-N link and no rel='next')."
            )

    if not candidate_href:
        raise RuntimeError("Could not determine URL pattern for pagination.")

    # normalize candidate href to absolute URL and add page size
    target_url = urljoin("https://www.chrono24.com", str(candidate_href))
    if f"pageSize={page_size}" not in target_url:
        target_url += f"&pageSize={page_size}"

    # Cache the URL pattern for future use
    _url_pattern_cache[cache_key] = (target_url, pattern_type)

    # Generate URL for the requested page
    if pattern_type == "showpage":
        final_url = target_url.replace(f"showpage=2", f"showpage={page}")
    elif pattern_type == "index":
        final_url = target_url.replace(f"index-2.htm", f"index-{page}.htm")
    else:  # pattern_type == "page"
        final_url = target_url.replace(f"-2.htm", f"-{page}.htm")

    return flaresolverr_get_html(final_url, headers=DEFAULT_HEADERS)


# Example usage:
if __name__ == "__main__":
    query = "Rolex DateJust"
    html_page2 = get_search_page_html(query, page=2, page_size=60, sortorder=5)
