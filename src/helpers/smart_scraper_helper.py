"""
VoiceMate Smart Scraper & Autonomous Web Extractor.
Leverages Scrapegraph-AI and Browser-Use patterns for robust, schema-driven
extraction of product prices, specs, and deep research summaries.
"""
import os
import re
import sys
import json
import logging
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from config import SCRAPEGRAPH_AI_REPO_DIR, BROWSER_USE_REPO_DIR

# Ensure local Scrapegraph-ai and browser-use repos are discovered in sys.path
for repo_dir in [SCRAPEGRAPH_AI_REPO_DIR, BROWSER_USE_REPO_DIR]:
    if repo_dir and repo_dir.exists() and str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))

logger = logging.getLogger("VoiceMate.SmartScraper")


class SmartWebScraper:
    """
    Intelligent Web Scraper and Deep Extractor inspired by Scrapegraph-AI & Browser-Use.
    Provides schema-based extraction, clean markdown text extraction,
    and fallback handling for JS-heavy or anti-bot web pages.
    """
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
    }

    @classmethod
    def fetch_page_html(cls, url: str, timeout: float = 6.0) -> Optional[str]:
        """Fetches raw HTML from a URL with browser-like user agent."""
        try:
            req = urllib.request.Request(url, headers=cls.DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                encoding = "utf-8"
                if "charset=" in content_type.lower():
                    encoding = content_type.lower().split("charset=")[-1].split(";")[0].strip()
                raw_bytes = response.read()
                return raw_bytes.decode(encoding, errors="replace")
        except Exception as e:
            logger.debug(f"Failed to fetch HTML for {url}: {e}")
            return None

    @classmethod
    def clean_html_to_text(cls, html: str) -> str:
        """Strips scripts, styles, and extra whitespace to extract readable text content."""
        if not html:
            return ""
        # Remove script and style tags
        text = re.sub(r"<(script|style|noscript|svg|canvas)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        # Convert header tags into markdown headers
        text = re.sub(r"<h([1-6])[^>]*>(.*?)</h\1>", r"\n# \2\n", text, flags=re.IGNORECASE)
        # Convert links to simple markdown links
        text = re.sub(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r" [\2](\1) ", text, flags=re.IGNORECASE)
        # Convert list items
        text = re.sub(r"<li[^>]*>(.*?)</li>", r"\n* \1", text, flags=re.IGNORECASE)
        # Remove remaining tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Unescape basic entities
        text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
        # Normalize whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    @classmethod
    def extract_product_data(cls, html_or_url: str, prompt: str = "") -> Dict[str, Any]:
        """
        Extracts structured product data (title, price, specs, warranty, availability).
        Implements Scrapegraph-AI pattern: Extract from HTML schema or DOM parsing.
        """
        html = html_or_url if "<html" in html_or_url.lower() or "<body" in html_or_url.lower() else cls.fetch_page_html(html_or_url)
        if not html:
            return {}

        clean_text = cls.clean_html_to_text(html)
        data: Dict[str, Any] = {
            "title": "",
            "price": 0.0,
            "currency": "BDT",
            "availability": "In Stock",
            "specifications": {},
            "warranty": "N/A",
            "seller": "",
            "raw_text_snippet": clean_text[:600]
        }

        # 1. Price extraction using currency regex patterns
        price_patterns = [
            r"(?:৳|BDT|TK|Tk|Price\s*:?)\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)",
            r"([0-9]{1,3}(?:,[0-9]{3})+)\s*(?:৳|BDT|TK|Tk)",
            r"\$\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)"
        ]
        for p in price_patterns:
            matches = re.findall(p, clean_text, flags=re.IGNORECASE)
            if matches:
                # Filter reasonable price numbers
                for m in matches:
                    clean_p = float(m.replace(",", ""))
                    if clean_p > 100:  # Ignore trivial numbers like 5, 10
                        data["price"] = clean_p
                        if "$" in p:
                            data["currency"] = "USD"
                        break
                if data["price"] > 0:
                    break

        # 2. Availability detection
        if re.search(r"out\s+of\s+stock|স্টক\s*আউট|not\s+available", clean_text, re.IGNORECASE):
            data["availability"] = "Out of Stock"
        elif re.search(r"in\s+stock|ইন\s*স্টক|available", clean_text, re.IGNORECASE):
            data["availability"] = "In Stock"

        # 3. Warranty extraction
        warranty_match = re.search(r"([0-9]+\s*(?:year|yr|month|মাস|বছর)\s*(?:brand|official)?\s*warranty)", clean_text, re.IGNORECASE)
        if warranty_match:
            data["warranty"] = warranty_match.group(1).strip()

        # 4. Extract specifications from key-value pairs
        spec_lines = re.findall(r"^(RAM|Processor|Storage|Display|Graphics|Battery|Camera|OS)\s*[:\-]\s*(.+)$", clean_text, re.MULTILINE | re.IGNORECASE)
        for k, v in spec_lines:
            data["specifications"][k.capitalize()] = v.strip()

        return data

    @classmethod
    def deep_search_query(cls, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Executes a web search and scrapes the actual target pages to get full context
        (Autonomous Deep Research Pattern from Browser-Use).
        """
        results = []
        encoded = urllib.parse.quote(query.strip())
        search_url = f"https://html.duckduckgo.com/html/?q={encoded}"

        html = cls.fetch_page_html(search_url)
        if not html:
            return results

        # Parse links and titles
        link_matches = re.findall(r'<h2 class="result__title">\s*<a class="result__url"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
        snippet_matches = re.findall(r'<a class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)

        for i in range(min(len(link_matches), num_results)):
            link, raw_title = link_matches[i]
            title = re.sub(r"<[^>]+>", "", raw_title).strip()
            
            # Unescape duckduckgo redirect URL if needed
            if "uddg=" in link:
                parsed_url = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get("uddg")
                if parsed_url:
                    link = parsed_url[0]

            snippet = ""
            if i < len(snippet_matches):
                snippet = re.sub(r"<[^>]+>", "", snippet_matches[i][1]).strip()

            item = {
                "title": title,
                "url": link,
                "snippet": snippet,
                "page_content": ""
            }

            # Autonomously visit the page to extract full content (deep research)
            try:
                page_html = cls.fetch_page_html(link, timeout=4.0)
                if page_html:
                    cleaned_body = cls.clean_html_to_text(page_html)
                    item["page_content"] = cleaned_body[:2500]  # Store first 2500 chars of authentic content
            except Exception:
                pass

            results.append(item)

        return results
