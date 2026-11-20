"""
VoiceMate Product Research & Price Comparison Agent.
Provides intelligent product search, multi-store price comparison,
specification extraction, and follow-up conversational shopping assistance.
"""
from src.product_agent.product_models import ProductItem, PriceComparisonResult, ProductSearchFilter
from src.product_agent.product_scraper import ProductScraper
from src.product_agent.price_comparator import PriceComparator
from src.product_agent.product_controller import ProductController
from src.product_agent.product_task_runner import ProductTaskRunner

__all__ = [
    "ProductItem",
    "PriceComparisonResult",
    "ProductSearchFilter",
    "ProductScraper",
    "PriceComparator",
    "ProductController",
    "ProductTaskRunner"
]
