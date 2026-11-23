"""
VoiceMate Product Agent - Product Data Models.
Defines structured schemas for products, price comparisons, specifications, and search filters.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class ProductItem:
    """
    Represents an individual verified product listing from a retailer or search engine.
    """
    name: str
    brand: str
    model: str
    price: float
    currency: str = "BDT"
    seller: str = "Unknown"
    product_url: str = ""
    original_price: Optional[float] = None
    specifications: Dict[str, str] = field(default_factory=dict)
    availability: str = "In Stock"  # 'In Stock', 'Out of Stock', 'Pre-order', 'Unavailable'
    rating: Optional[float] = None
    shipping_info: Optional[str] = None
    last_checked: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    is_verified: bool = True
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "brand": self.brand,
            "model": self.model,
            "price": self.price,
            "currency": self.currency,
            "seller": self.seller,
            "product_url": self.product_url,
            "original_price": self.original_price,
            "specifications": self.specifications,
            "availability": self.availability,
            "rating": self.rating,
            "shipping_info": self.shipping_info,
            "last_checked": self.last_checked,
            "is_verified": self.is_verified,
            "notes": self.notes
        }

    def format_price_display(self) -> str:
        """Formats price with currency symbol (e.g. ৳54,500)."""
        val_str = f"{int(self.price):,}"
        if self.currency.upper() in ["BDT", "TK", "TAKA"]:
            return f"৳{val_str}"
        return f"{self.currency} {val_str}"

    def format_specs_display(self) -> str:
        """Formats key specifications into a readable string."""
        if not self.specifications:
            return "স্পেসিফিকেশন তথ্য পাওয়া যায়নি"
        parts = []
        for k, v in self.specifications.items():
            parts.append(f"{k}: {v}")
        return ", ".join(parts)


@dataclass
class PriceComparisonResult:
    """
    Represents comparison analysis across multiple sellers/retailers.
    """
    product_query: str
    items: List[ProductItem] = field(default_factory=list)
    cheapest_item: Optional[ProductItem] = None
    highest_item: Optional[ProductItem] = None
    price_difference: float = 0.0
    spec_differences: List[str] = field(default_factory=list)
    cheapest_seller: str = ""
    summary_bn: str = ""
    summary_en: str = ""
    min_price: float = 0.0
    max_price: float = 0.0
    avg_price: float = 0.0
    country_market: str = "Bangladesh"
    sources_checked: int = 0
    formatted_report: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_query": self.product_query,
            "total_listings": len(self.items),
            "sources_checked": self.sources_checked or len(self.items),
            "country_market": self.country_market,
            "min_price": self.min_price or (self.cheapest_item.price if self.cheapest_item else 0.0),
            "max_price": self.max_price or (self.highest_item.price if self.highest_item else 0.0),
            "avg_price": self.avg_price,
            "price_difference": self.price_difference,
            "cheapest_item": self.cheapest_item.to_dict() if self.cheapest_item else None,
            "highest_item": self.highest_item.to_dict() if self.highest_item else None,
            "spec_differences": self.spec_differences,
            "cheapest_seller": self.cheapest_seller,
            "summary_bn": self.summary_bn,
            "summary_en": self.summary_en,
            "formatted_report": self.formatted_report,
            "items": [item.to_dict() for item in self.items]
        }


@dataclass
class ProductSearchFilter:
    """
    Defines extraction parameters for product search and filtering.
    """
    query: str
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None  # 'laptop', 'phone', 'tablet', etc.
    max_budget: Optional[float] = None
    min_budget: Optional[float] = None
    currency: str = "BDT"
    retailer: Optional[str] = None
    specs: Dict[str, str] = field(default_factory=dict)
