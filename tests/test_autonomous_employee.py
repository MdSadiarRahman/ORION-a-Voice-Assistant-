"""
VoiceMate Autonomous AI Assistant - End-to-End Pipeline Test Suite.
Validates the core autonomous pipelines:
1. Headless Web Research & Academic Source Synthesis
2. Assignment Solver & Pure-Python DOCX Export
3. Intent Tool Registry (Local PC File Search & Live Weather)
4. End-to-End Decision Engine Assignment & Research Workflows
"""
import unittest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.assignment_agent.assignment_controller import AssignmentController
from src.helpers.web_research_helper import WebResearchHelper
from src.intelligence.decision_engine import HybridDecisionEngine
from src.intelligence.tool_registry import ToolRegistry


class TestAutonomousEmployee(unittest.TestCase):
    """Validates VoiceMate's core autonomous workflows."""

    def setUp(self):
        self.engine = HybridDecisionEngine()

    def test_01_deep_internet_research_with_citations(self):
        """Test 1: Headless Web Research helper returns citations and facts."""
        res = WebResearchHelper.conduct_academic_research("Quantum Computing")
        self.assertTrue(res["success"])
        report = res["report"]
        self.assertIn("summary", report)
        self.assertGreater(len(report["sources"]), 0)
        self.assertGreater(len(report["key_facts"]), 0)
        for s in report["sources"]:
            self.assertTrue(s["url"].startswith("http"))
        print(f"\n[Test 1 PASS] Web Research -> Citations: {len(report['sources'])} sources.")

    def test_02_assignment_solver_and_pure_docx_export(self):
        """Test 2: Assignment Agent parses questions, solves them, and exports .docx + .md."""
        res = AssignmentController.execute_assignment_workflow("test_assignment.md")
        self.assertTrue(res["success"])
        self.assertGreater(res["parsed_assignment"]["total_questions"], 0)
        exported = res["exported_files"]

        docx_path = Path(exported["docx_path"])
        self.assertTrue(docx_path.exists())
        self.assertGreater(docx_path.stat().st_size, 500)

        md_path = Path(exported["md_path"])
        self.assertTrue(md_path.exists())
        self.assertGreater(md_path.stat().st_size, 200)
        print(f"\n[Test 2 PASS] Assignment Agent -> Questions: {res['parsed_assignment']['total_questions']}, DOCX: {docx_path.name}.")

    def test_03_tool_registry_file_search_and_weather(self):
        """Test 3: ToolRegistry executes local file search and weather lookup cleanly."""
        tr = ToolRegistry()
        file_res = tr.execute("SEARCH_LOCAL_FILE", query="test_sample")
        self.assertTrue(file_res.get("ok"))
        self.assertIn("test_sample", file_res.get("reply", ""))

        weather_res = tr.execute("GET_WEATHER", query="ঢাকার আবহাওয়া কেমন?")
        self.assertTrue(weather_res.get("ok"))
        self.assertTrue(weather_res.get("reply"))
        print("\n[Test 3 PASS] ToolRegistry File Search & Weather verified.")

    def test_04_end_to_end_decision_engine_pipeline(self):
        """Test 4: Natural language commands trigger Assignment & Web Research pipelines."""
        cmd_res_report = "কোয়ান্টাম কম্পিউটিং কী? রিসার্চ রিপোর্ট দাও"
        intent_r, response_r = self.engine.process_query(cmd_res_report)
        self.assertEqual(intent_r.source, "web_research")
        self.assertIn("গবেষণামূলক", response_r)

        cmd_assign = "অ্যাসাইনমেন্ট সলভ করে docx ফাইলে সেভ করো"
        intent_a, response_a = self.engine.process_query(cmd_assign)
        self.assertEqual(intent_a.source, "assignment_agent")
        self.assertIn("docx_path", intent_a.parameters["assignment_result"]["exported_files"])
        self.assertIn("DOCX", response_a)
        print("\n[Test 4 PASS] End-to-End Assignment & Research Decision Engine pipeline verified.")


if __name__ == "__main__":
    unittest.main()
