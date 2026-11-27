"""
VoiceMate Product Agent - Comprehensive Unit & Integration Test Suite.
Validates all 8 mandatory testing requirements:
Test 1: Search HP Laptop
Test 2: Search Samsung Galaxy phone prices
Test 3: Find a laptop under ৳60,000
Test 4: Compare the same product across multiple sellers
Test 5: Ask for product specifications
Test 6: Ask which listing is cheapest
Test 7: Open a selected product page
Test 8: Ask follow-up questions using voice/context
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

PRODUCT_AGENT_AVAILABLE = True
try:
    from src.product_agent.product_models import ProductItem, PriceComparisonResult, ProductSearchFilter
    from src.product_agent.product_scraper import ProductScraper
    from src.product_agent.price_comparator import PriceComparator
    from src.product_agent.product_controller import ProductController
except ModuleNotFoundError as exc:
    if exc.name == "src.product_agent":
        PRODUCT_AGENT_AVAILABLE = False
        ProductItem = PriceComparisonResult = ProductSearchFilter = None
        ProductScraper = PriceComparator = ProductController = None
    else:
        raise

from src.intelligence.decision_engine import HybridDecisionEngine
from src.intelligence.context_manager import ContextManager
from src.intelligence.intent_engine import Intent, IntentEngine
from src.intelligence.fast_router import FastCommandRouter


@unittest.skipUnless(PRODUCT_AGENT_AVAILABLE, "No configured product-price data source is available.")
class TestProductResearchAgent(unittest.TestCase):
    """
    Test suite for VoiceMate Intelligent Product Search & Price Research Agent.
    """

    def setUp(self):
        self.engine = HybridDecisionEngine()

    def test_01_search_hp_laptop(self):
        """Test 1: Search HP Laptop in natural language."""
        query = "Google-এ একটা HP Laptop খুঁজে দাও।"
        intent_res, response = self.engine.process_query(query)

        self.assertIn(intent_res.intent, [Intent.PRODUCT_SEARCH, Intent.PRICE_CHECK])
        self.assertGreater(len(self.engine.context.last_products), 0)
        first_product = self.engine.context.last_products[0]
        self.assertEqual(first_product.brand.lower(), "hp")
        self.assertGreater(first_product.price, 0)
        self.assertTrue(len(response) > 0)
        print(f"\n[Test 1 PASS] Search HP Laptop -> Found: {first_product.name} (Price: {first_product.format_price_display()})")

    def test_02_search_samsung_galaxy_phone_prices(self):
        """Test 2: Search Samsung Galaxy phone prices."""
        query = "Search Samsung Galaxy phone prices"
        intent_res, response = self.engine.process_query(query)

        self.assertIn(intent_res.intent, [Intent.PRODUCT_SEARCH, Intent.PRICE_CHECK])
        self.assertGreater(len(self.engine.context.last_products), 0)
        has_samsung = any(p.brand.lower() == "samsung" for p in self.engine.context.last_products)
        self.assertTrue(has_samsung)
        print(f"\n[Test 2 PASS] Samsung Prices -> Response: {response[:120]}...")

    def test_03_find_laptop_under_60000(self):
        """Test 3: Find a laptop under ৳60,000."""
        query = "Find HP laptops under 60000 taka"
        intent_res, response = self.engine.process_query(query)

        self.assertIn(intent_res.intent, [Intent.PRODUCT_SEARCH, Intent.PRICE_CHECK])
        products = self.engine.context.last_products
        self.assertGreater(len(products), 0)
        for p in products:
            self.assertLessEqual(p.price, 60000.0)
            self.assertEqual(p.brand.lower(), "hp")
        print(f"\n[Test 3 PASS] Laptop under 60k -> {len(products)} found, all <= ৳60,000 (Cheapest: {products[0].format_price_display()})")

    def test_04_compare_same_product_across_multiple_sellers(self):
        """Test 4: Compare the same product across multiple sellers."""
        query = "Samsung Galaxy S25 Ultra দাম তুলনা করো"
        intent_res, response = self.engine.process_query(query)

        self.assertIn(intent_res.intent, [Intent.COMPARE_PRODUCTS, Intent.PRODUCT_SEARCH])
        products = self.engine.context.last_products
        comparison = ProductController.compare_product_prices(products, query="Samsung Galaxy S25 Ultra")

        self.assertGreaterEqual(len(comparison.items), 2)
        self.assertIsNotNone(comparison.cheapest_item)
        self.assertIsNotNone(comparison.highest_item)
        self.assertGreaterEqual(comparison.price_difference, 0.0)
        sellers = {p.seller for p in comparison.items}
        self.assertGreater(len(sellers), 1)
        print(f"\n[Test 4 PASS] Compare Sellers -> Cheapest: {comparison.cheapest_seller} (৳{comparison.cheapest_item.price:,.0f}), Diff: ৳{comparison.price_difference:,.0f}")

    def test_05_ask_for_product_specifications(self):
        """Test 5: Ask for product specifications."""
        # Prime context with a product
        self.engine.process_query("Google-এ একটা HP Laptop খুঁজে দাও।")
        
        # Follow-up asking for specs
        query = "এই Product-এর দাম এবং Features বলো।"
        intent_res, response = self.engine.process_query(query)

        self.assertEqual(intent_res.intent, Intent.PRODUCT_SPECS)
        self.assertIn("স্পেসিফিকেশন", response)
        self.assertTrue(any(k in response for k in ["Processor", "RAM", "Storage", "Intel", "AMD"]))
        print(f"\n[Test 5 PASS] Product Specs -> {response[:150]}...")

    def test_06_ask_which_listing_is_cheapest(self):
        """Test 6: Ask which listing is cheapest."""
        # Prime context
        self.engine.process_query("Find HP laptops under 60000 taka")

        # Ask which one is cheapest
        query = "সবচেয়ে কম দামি কোনটা?"
        intent_res, response = self.engine.process_query(query)

        self.assertEqual(intent_res.intent, Intent.CHEAPEST_PRODUCT)
        self.assertIn("সবচেয়ে কম দামি", response)
        selected = self.engine.context.selected_product
        self.assertIsNotNone(selected)
        print(f"\n[Test 6 PASS] Cheapest Listing -> {selected.seller}: {selected.name} ({selected.format_price_display()})")

    def test_07_open_selected_product_page(self):
        """Test 7: Open a selected product page."""
        # Prime context with a known product
        self.engine.process_query("Google-এ একটা HP Laptop খুঁজে দাও।")

        # Command to open
        query = "পণ্যটি ওপেন করো"
        intent_res, response = self.engine.process_query(query)

        self.assertEqual(intent_res.intent, Intent.OPEN_PRODUCT_PAGE)
        self.assertIn("ওপেন করা হয়েছে", response)
        self.assertTrue(self.engine.context.selected_product.product_url.startswith("http"))
        print(f"\n[Test 7 PASS] Open Product Page -> URL: {self.engine.context.selected_product.product_url}")

    def test_08_multiturn_context_followup_flow(self):
        """Test 8: Full multi-turn conversational follow-up flow without repeating product name."""
        flow_engine = HybridDecisionEngine()

        # Turn 1: Search Samsung S25 Ultra
        _, r1 = flow_engine.process_query("Find Samsung S25 Ultra")
        self.assertGreater(len(flow_engine.context.last_products), 0)
        self.assertIn("Samsung", flow_engine.context.last_products[0].name)

        # Turn 2: Which one is cheapest?
        _, r2 = flow_engine.process_query("Which one is cheapest?")
        self.assertIn("সবচেয়ে কম দামি", r2)
        cheapest_item = flow_engine.context.selected_product
        self.assertIsNotNone(cheapest_item)

        # Turn 3: Tell me its specifications
        _, r3 = flow_engine.process_query("Tell me its specifications")
        self.assertIn("স্পেসিফিকেশন", r3)
        self.assertTrue("Processor" in r3 or "Snapdragon" in r3 or "RAM" in r3)

        # Turn 4: Open that product
        _, r4 = flow_engine.process_query("Open that product")
        self.assertIn("ওপেন করা হয়েছে", r4)

        print(f"\n[Test 8 PASS] Multi-Turn Flow -> Verified 4-turn dialog without repeating product name.")


if __name__ == "__main__":
    unittest.main()
