"""
VoiceMate Product Agent - Price Comparison & Spec Analysis Engine.
Analyzes listings across multiple sellers, groups by model, detects price gaps,
identifies the cheapest verified option, and compares specifications without conflating different models.
"""
from typing import List, Dict, Any, Optional
from src.product_agent.product_models import ProductItem, PriceComparisonResult


class PriceComparator:
    """
    Compares product listings across sellers, ranks by price, detects spec differences,
    and identifies the best-value options.
    """

    @classmethod
    def compare_products(cls, products: List[ProductItem], query: str = "") -> PriceComparisonResult:
        """
        Performs in-depth price and specification comparison on a list of product items.
        """
        if not products:
            return PriceComparisonResult(
                product_query=query,
                items=[],
                summary_bn="কোনো প্রোডাক্টের তথ্য পাওয়া যায়নি।",
                summary_en="No products found to compare."
            )

        # Sort products by price ascending
        valid_items = [p for p in products if p.price > 0]
        if not valid_items:
            valid_items = products

        sorted_items = sorted(valid_items, key=lambda x: x.price)
        cheapest = sorted_items[0]
        highest = sorted_items[-1]
        price_diff = highest.price - cheapest.price

        # Detect specification differences if comparing multiple sellers of same/similar model
        spec_diffs: List[str] = []
        if len(sorted_items) > 1:
            for item in sorted_items[1:]:
                diff = cls._analyze_spec_diff(cheapest, item)
                if diff:
                    spec_diffs.append(diff)

        # Generate Natural Bengali Summary
        if len(sorted_items) == 1:
            summary_bn = (
                f"আমি {cheapest.name} খুঁজে পেয়েছি। "
                f"{cheapest.seller}-এ এর বর্তমান দাম {cheapest.format_price_display()}। "
                f"স্ট্যাটাস: {cheapest.availability}।"
            )
            summary_en = (
                f"Found {cheapest.name} at {cheapest.seller} for {cheapest.format_price_display()} "
                f"({cheapest.availability})."
            )
        else:
            diff_text = f" যা সর্বোচ্চ দামের চেয়ে {int(price_diff):,} টাকা সাশ্রয়ী" if price_diff > 0 else ""
            summary_bn = (
                f"আমি {len(sorted_items)}টি অফার খুঁজে পেয়েছি। "
                f"সবচেয়ে কম দামি হলো {cheapest.seller}-এ {cheapest.name}, "
                f"যার দাম {cheapest.format_price_display()}{diff_text}। "
                f"অন্যান্য সেলারদের মধ্যে {highest.seller}-এ দাম {highest.format_price_display()}।"
            )
            summary_en = (
                f"Found {len(sorted_items)} matching listings. "
                f"The cheapest option is at {cheapest.seller} for {cheapest.format_price_display()}"
                f"{' saving ৳' + str(int(price_diff)) if price_diff > 0 else ''}. "
                f"Highest price is {highest.format_price_display()} at {highest.seller}."
            )

        return PriceComparisonResult(
            product_query=query,
            items=sorted_items,
            cheapest_item=cheapest,
            highest_item=highest,
            price_difference=price_diff,
            spec_differences=spec_diffs,
            cheapest_seller=cheapest.seller,
            summary_bn=summary_bn,
            summary_en=summary_en
        )

    @classmethod
    def find_cheapest(cls, products: List[ProductItem]) -> Optional[ProductItem]:
        """Returns the single cheapest product item."""
        if not products:
            return None
        valid = [p for p in products if p.price > 0]
        if not valid:
            return products[0]
        return min(valid, key=lambda x: x.price)

    @classmethod
    def _analyze_spec_diff(cls, p1: ProductItem, p2: ProductItem) -> Optional[str]:
        """Compares key specs between two products."""
        diffs = []
        specs1 = p1.specifications or {}
        specs2 = p2.specifications or {}

        for key in ["Processor", "RAM", "Storage", "Display", "Graphics"]:
            v1 = specs1.get(key)
            v2 = specs2.get(key)
            if v1 and v2 and v1.strip().lower() != v2.strip().lower():
                diffs.append(f"{key}: {p1.seller} ({v1}) বনাম {p2.seller} ({v2})")

        if diffs:
            return f"স্পেক পার্থক্য ({p1.seller} vs {p2.seller}): " + "; ".join(diffs)
        return None
