"""Search retailer listings and compare prices that are present in their pages."""

import html
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from html.parser import HTMLParser
from typing import Callable, Optional
from urllib.parse import urljoin, urlparse


@dataclass(frozen=True)
class Retailer:
    name: str
    host: str
    search_url: str


@dataclass(frozen=True)
class ProductPrice:
    name: str
    price_bdt: float
    price_text: str
    retailer: str
    url: str


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    children: list[object] = field(default_factory=list)


class _ProductHTMLParser(HTMLParser):
    VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("root", {})
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        node = _Node(tag, {key: value or "" for key, value in attrs})
        self.stack[-1].children.append(node)
        if tag not in self.VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        self.stack[-1].children.append(_Node(tag, {key: value or "" for key, value in attrs}))

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.stack[-1].children.append(data)


class ProductPriceSearch:
    RETAILERS = (
        Retailer(
            "Star Tech",
            "startech.com.bd",
            "https://www.startech.com.bd/index.php?route=product/search&search={query}",
        ),
        Retailer(
            "UCC",
            "ucc.com.bd",
            "https://www.ucc.com.bd/index.php?route=product/search&search={query}",
        ),
        Retailer(
            "Global Brand",
            "globalbrand.com.bd",
            "https://www.globalbrand.com.bd/index.php?route=product/search&search={query}",
        ),
        Retailer(
            "Ryans",
            "ryans.com",
            "https://www.ryans.com/search?search={query}",
        ),
    )
    MAX_RESULTS_PER_RETAILER = 5
    REQUEST_TIMEOUT_SECONDS = 12
    ACCESSORY_TERMS = {
        "adapter", "bag", "battery", "cable", "case", "charger", "connector",
        "cover", "cooler", "fan", "hinge", "keyboard", "mouse",
        "panel", "protector", "replacement", "screen", "sleeve", "stand",
        "কভার", "কেস", "চার্জার",
    }
    PRODUCT_CATEGORY_ALIASES = (
        {"laptop", "notebook", "ল্যাপটপ"},
        {"phone", "smartphone", "mobile", "মোবাইল"},
        {"tablet"},
        {"monitor", "display"},
        {"printer"},
        {"camera"},
    )

    @classmethod
    def search(
        cls,
        query: str,
        fetcher: Optional[Callable[[Retailer, str], str]] = None,
    ) -> dict:
        clean_query = query.strip()
        if not clean_query:
            return {
                "success": False,
                "query": query,
                "prices": [],
                "source_errors": [],
                "sources_without_matches": [],
                "message": "পণ্যের নাম বা model দিন।",
            }

        get_page = fetcher or cls._fetch_search_page
        prices: list[ProductPrice] = []
        source_errors: list[str] = []
        sources_without_matches: list[str] = []

        for retailer in cls.RETAILERS:
            try:
                page_url = retailer.search_url.format(query=urllib.parse.quote_plus(clean_query))
                page_html = get_page(retailer, page_url)
                retailer_prices = cls.parse_search_page(page_html, retailer, clean_query)
                if retailer_prices:
                    prices.extend(retailer_prices)
                else:
                    sources_without_matches.append(retailer.name)
            except (OSError, TimeoutError, ValueError, urllib.error.URLError) as exc:
                source_errors.append(f"{retailer.name}: {exc}")

        unique_prices: dict[tuple[str, str], ProductPrice] = {}
        for item in prices:
            unique_prices[(item.retailer, item.url)] = item
        sorted_prices = sorted(unique_prices.values(), key=lambda item: item.price_bdt)

        if not sorted_prices:
            error_note = f" Source access errors: {'; '.join(source_errors)}." if source_errors else ""
            no_match_note = (
                f" Matching priced listings were not found at: {', '.join(sources_without_matches)}."
                if sources_without_matches else ""
            )
            return {
                "success": False,
                "query": clean_query,
                "prices": [],
                "source_errors": source_errors,
                "sources_without_matches": sources_without_matches,
                "checked_at": datetime.now().astimezone().isoformat(timespec="minutes"),
                "message": f"কোনো retailer page থেকে যাচাইযোগ্য price পাওয়া যায়নি।{no_match_note}{error_note}",
            }

        source_count = len({item.retailer for item in sorted_prices})
        checked_at = datetime.now().astimezone().isoformat(timespec="minutes")
        lines = [
            f"{item.name} — ৳{item.price_text} — {item.retailer}\n{item.url}"
            for item in sorted_prices[:10]
        ]
        if source_count >= 2:
            lowest = sorted_prices[0]
            summary = (
                f"{source_count}টি retailer source-এ '{clean_query}'-এর দাম পাওয়া গেছে। "
                f"পাওয়া ফলাফলের মধ্যে সবচেয়ে কম ৳{lowest.price_text} ({lowest.retailer}); "
                f"দাম ও stock বদলাতে পারে। যাচাইয়ের সময়: {checked_at}।"
            )
        else:
            summary = (
                f"'{clean_query}'-এর price শুধু {sorted_prices[0].retailer} source-এ পাওয়া গেছে; "
                f"তাই বহু-দোকানের তুলনা করা যাচ্ছে না। যাচাইয়ের সময়: {checked_at}।"
            )
        if sources_without_matches:
            summary += (
                " মেলা price listing পাওয়া যায়নি: "
                f"{', '.join(sources_without_matches)}."
            )
        if source_errors:
            summary += f" অন্য কিছু source খোলা যায়নি: {'; '.join(source_errors)}."
        return {
            "success": True,
            "query": clean_query,
            "prices": sorted_prices,
            "source_errors": source_errors,
            "sources_without_matches": sources_without_matches,
            "checked_at": checked_at,
            "message": summary + "\n\n" + "\n\n".join(lines),
        }

    @classmethod
    def _fetch_search_page(cls, retailer: Retailer, url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(request, timeout=cls.REQUEST_TIMEOUT_SECONDS) as response:
            final_url = response.geturl()
            if not cls._is_allowed_url(final_url, retailer.host):
                raise ValueError("retailer redirected outside its allowed domain")
            return response.read(2_000_000).decode("utf-8", errors="replace")

    @classmethod
    def parse_search_page(cls, page_html: str, retailer: Retailer, query: str) -> list[ProductPrice]:
        parser = _ProductHTMLParser()
        parser.feed(page_html)
        query_tokens = cls._tokens(query)
        cards = [
            node for node in cls._walk(parser.root)
            if node.tag in {"div", "li", "article"}
            and set(node.attrs.get("class", "").lower().split())
            & {"product-thumb", "p-item", "product-card", "product-item", "product-layout"}
        ]

        found: list[ProductPrice] = []
        seen_urls: set[str] = set()
        for card in cards:
            links = [
                node for node in cls._walk(card)
                if node.tag == "a" and node.attrs.get("href")
            ]
            link_data = []
            for node in links:
                href = urljoin("https://" + retailer.host, node.attrs["href"])
                if not cls._is_allowed_url(href, retailer.host):
                    continue
                title = cls._node_text(node).strip()
                if not title:
                    image = next(
                        (child for child in cls._walk(node) if child.tag == "img" and child.attrs.get("alt")),
                        None,
                    )
                    title = image.attrs["alt"].strip() if image else ""
                if title and title.lower() not in {"buy now", "compare", "add to cart"}:
                    link_data.append((title, href, cls._match_score(query_tokens, cls._tokens(title))))
            if not link_data:
                continue
            title, product_url, score = max(link_data, key=lambda item: item[2])
            if not cls._is_relevant(query_tokens, cls._tokens(title), score):
                continue
            if product_url in seen_urls:
                continue

            price = cls._get_current_price(card)
            if not price:
                continue
            seen_urls.add(product_url)
            found.append(
                ProductPrice(
                    name=title,
                    price_bdt=price[0],
                    price_text=price[1],
                    retailer=retailer.name,
                    url=product_url,
                )
            )
            if len(found) >= cls.MAX_RESULTS_PER_RETAILER:
                break
        return found

    @classmethod
    def _get_current_price(cls, card: _Node) -> Optional[tuple[float, str]]:
        candidates: list[tuple[int, str]] = []
        for node in cls._walk(card):
            classes = node.attrs.get("class", "").lower().split()
            if not any("price" in class_name for class_name in classes):
                continue
            if any(term in " ".join(classes) for term in ("old", "regular", "was", "strike")):
                continue
            text = cls._node_text(node).strip()
            if text:
                priority = 0 if any(term in " ".join(classes) for term in ("new", "normal", "special", "current")) else 1
                candidates.append((priority, text))

        for _, text in sorted(candidates, key=lambda item: item[0]):
            parsed = cls._parse_bdt_price(text)
            if parsed:
                return parsed
        return None

    @staticmethod
    def _parse_bdt_price(text: str) -> Optional[tuple[float, str]]:
        decoded = html.unescape(text)
        bengali_digits = "০১২৩৪৫৬৭৮৯"
        decoded = decoded.translate(str.maketrans(bengali_digits, "0123456789"))
        match = re.search(
            r"(?:৳|BDT|Tk\.?)\s*([\d,]+(?:\.\d{1,2})?)|([\d,]+(?:\.\d{1,2})?)\s*(?:৳|BDT|Tk\.?)",
            decoded,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        amount_text = (match.group(1) or match.group(2)).replace(",", "")
        try:
            amount = float(amount_text)
        except ValueError:
            return None
        if amount <= 0:
            return None
        return amount, f"{amount:,.2f}".rstrip("0").rstrip(".")

    @staticmethod
    def _walk(node: _Node):
        yield node
        for child in node.children:
            if isinstance(child, _Node):
                yield from ProductPriceSearch._walk(child)

    @classmethod
    def _node_text(cls, node: _Node) -> str:
        parts: list[str] = []
        for child in node.children:
            if isinstance(child, str):
                parts.append(child)
            else:
                parts.append(cls._node_text(child))
        return " ".join(part for part in parts if part).strip()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+|[\u0980-\u09ff]+", text.lower()))

    @staticmethod
    def _match_score(query_tokens: set[str], title_tokens: set[str]) -> float:
        if not query_tokens:
            return 0.0
        return len(query_tokens & title_tokens) / len(query_tokens)

    @classmethod
    def _is_relevant(cls, query_tokens: set[str], title_tokens: set[str], score: float) -> bool:
        if not query_tokens:
            return False
        if not (query_tokens & cls.ACCESSORY_TERMS) and title_tokens & cls.ACCESSORY_TERMS:
            return False
        for aliases in cls.PRODUCT_CATEGORY_ALIASES:
            if query_tokens & aliases and not title_tokens & aliases:
                return False
        numeric_tokens = {token for token in query_tokens if any(char.isdigit() for char in token)}
        if not numeric_tokens.issubset(title_tokens):
            return False
        return score >= 0.5

    @staticmethod
    def _is_allowed_url(url: str, retailer_host: str) -> bool:
        host = (urlparse(url).hostname or "").lower()
        expected = retailer_host.lower()
        return host == expected or host.endswith("." + expected)
