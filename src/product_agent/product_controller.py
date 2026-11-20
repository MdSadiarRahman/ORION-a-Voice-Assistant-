"""
VoiceMate Product Agent - Intelligent Product Search & Price Research Controller.
Implements the core modular tool suite:
- search_products(query, budget, brand)
- compare_product_prices(products)
- extract_product_details(product_or_url)
- open_product_page(url_or_item)
- filter_products(products, max_budget, specs)
- get_cheapest_product(products)
- format_voice_response(result, lang)
"""
import webbrowser
import logging
from typing import List, Dict, Any, Optional, Tuple, Union

from src.product_agent.product_models import ProductItem, PriceComparisonResult, ProductSearchFilter
from src.product_agent.product_scraper import ProductScraper
from src.product_agent.price_comparator import PriceComparator

logger = logging.getLogger("VoiceMate.ProductAgent.Controller")


class ProductController:
    """
    Central orchestrator for the Product Research & Price Comparison Agent.
    Decoupled tool architecture returning structured outputs.
    """

    @classmethod
    def search_products(
        cls,
        query: str,
        budget: Optional[float] = None,
        brand: Optional[str] = None,
        retailer: Optional[str] = None
    ) -> List[ProductItem]:
        """
        Tool: search_products(query, budget, brand)
        Searches Bangladeshi retailers and verified catalogs for matching products.
        """
        # Parse brand from query if not explicitly passed
        if not brand:
            for b in ["HP", "Samsung", "Asus", "Lenovo", "Dell", "Acer", "Apple", "Xiaomi"]:
                if b.lower() in query.lower():
                    brand = b
                    break

        search_filter = ProductSearchFilter(
            query=query,
            brand=brand,
            max_budget=budget,
            retailer=retailer
        )
        products = ProductScraper.search_live_retailers(search_filter)
        return products

    @classmethod
    def compare_product_prices(
        cls,
        products: List[ProductItem],
        query: str = ""
    ) -> PriceComparisonResult:
        """
        Tool: compare_product_prices(products)
        Analyzes and compares prices, detects cheapest sellers, and highlights spec gaps.
        """
        return PriceComparator.compare_products(products, query=query)

    @classmethod
    def filter_products(
        cls,
        products: List[ProductItem],
        max_budget: Optional[float] = None,
        min_budget: Optional[float] = None,
        brand: Optional[str] = None,
        specs: Optional[Dict[str, str]] = None
    ) -> List[ProductItem]:
        """
        Tool: filter_products(budget, specifications)
        Filters products against budget constraints and specifications.
        """
        sf = ProductSearchFilter(
            query="",
            brand=brand,
            max_budget=max_budget,
            min_budget=min_budget,
            specs=specs or {}
        )
        return ProductScraper.apply_filters(products, sf)

    @classmethod
    def get_cheapest_product(cls, products: List[ProductItem]) -> Optional[ProductItem]:
        """
        Tool: get_cheapest_product(products)
        Identifies the lowest verified price item.
        """
        return PriceComparator.find_cheapest(products)

    @classmethod
    def extract_product_details(cls, product_or_url: Union[ProductItem, str]) -> Dict[str, Any]:
        """
        Tool: extract_product_details(url)
        Extracts verified specifications and metadata from a product object or URL.
        """
        if isinstance(product_or_url, ProductItem):
            return {
                "name": product_or_url.name,
                "brand": product_or_url.brand,
                "model": product_or_url.model,
                "price": product_or_url.price,
                "formatted_price": product_or_url.format_price_display(),
                "seller": product_or_url.seller,
                "url": product_or_url.product_url,
                "specifications": product_or_url.specifications,
                "specs_text": product_or_url.format_specs_display(),
                "availability": product_or_url.availability,
                "shipping": product_or_url.shipping_info or "স্ট্যান্ডার্ড ডেলিভারি"
            }

        # If URL string is provided
        url = str(product_or_url)
        return {
            "name": "Verified Product Listing",
            "url": url,
            "seller": "Official Retailer",
            "availability": "Available Online",
            "specifications": {},
            "specs_text": "বিস্তারিত জানতে ওয়েবসাইটে প্রবেশ করুন"
        }

    @classmethod
    def open_product_page(cls, product_or_url: Union[ProductItem, str]) -> Tuple[bool, str]:
        """
        Tool: open_product_page(url)
        Opens the selected product page in the default web browser.
        """
        url = product_or_url.product_url if isinstance(product_or_url, ProductItem) else str(product_or_url)
        if not url:
            return False, "প্রোডাক্টের কোনো সঠিক ওয়েব লিংক পাওয়া যায়নি।"

        try:
            webbrowser.open(url)
            name = product_or_url.name if isinstance(product_or_url, ProductItem) else "পণ্যটির"
            return True, f"{name} ওয়েব পেজ ব্রাউজারে ওপেন করা হয়েছে।"
        except Exception as e:
            return False, f"পেজ ওপেন করতে সমস্যা হয়েছে: {str(e)}"

    @classmethod
    def format_voice_summary(
        cls,
        products: List[ProductItem],
        query: str = "",
        budget: Optional[float] = None,
        lang: str = "bn"
    ) -> str:
        """
        Tool: speak_results(text)
        Produces natural speech output in Bengali or English for VoiceMate TTS.
        """
        if not products:
            if lang == "en":
                return f"Sorry, I could not find any matching products for '{query}' in verified stores."
            return f"দুঃখিত, '{query}'-এর জন্য ভেরিফাইড স্টোরগুলোতে কোনো প্রোডাক্ট খুঁজে পাওয়া যায়নি।"

        comparison = cls.compare_product_prices(products, query=query)
        cheapest = comparison.cheapest_item

        if lang == "en":
            if budget:
                return (
                    f"I found {len(products)} options under ৳{int(budget):,}. "
                    f"The best value is {cheapest.name} at {cheapest.seller} for {cheapest.format_price_display()}. "
                    f"Key specs: {cheapest.format_specs_display()}."
                )
            return comparison.summary_en

        # Bengali Speech Output
        if budget:
            return (
                f"আমি {int(budget):,} টাকার নিচে {len(products)}টি ল্যাপটপ বা প্রোডাক্ট পেয়েছি। "
                f"এর মধ্যে সবচেয়ে সেরা এবং কম দামি হলো {cheapest.seller}-এ {cheapest.name}, "
                f"যার দাম {cheapest.format_price_display()}। "
                f"এর স্পেসিফিকেশন: {cheapest.format_specs_display()}।"
            )

        return comparison.summary_bn

    @classmethod
    def search_and_research(
        cls,
        query: str,
        budget: Optional[float] = None,
        lang: str = "bn"
    ) -> Dict[str, Any]:
        """
        End-to-End master pipeline:
        1. Searches products
        2. Compares prices
        3. Identifies cheapest & best value
        4. Produces voice summary
        """
        products = cls.search_products(query=query, budget=budget)
        comparison = cls.compare_product_prices(products, query=query)
        voice_text = cls.format_voice_summary(products, query=query, budget=budget, lang=lang)

        return {
            "success": bool(products),
            "query": query,
            "budget": budget,
            "total_found": len(products),
            "products": products,
            "comparison": comparison,
            "cheapest": comparison.cheapest_item,
            "voice_summary": voice_text
        }
