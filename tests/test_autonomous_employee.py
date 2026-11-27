"""
VoiceMate Autonomous AI Employee - End-to-End System Integration Test Suite.
Validates the complete autonomous agent pipeline:
1. Task Planner Goal Decomposition
2. Agent-to-Agent Data Passing
3. Deep Internet Research with Citations
4. Assignment Solver & Pure-Python DOCX Export
5. Full-Stack Website Scaffolding & Local Server Verification
6. Tool Registry & Human-In-The-Loop Approval Gates
"""
import unittest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent_brain.task_planner import TaskPlanner, TaskDomain, StepStatus
from src.agent_brain.tool_registry import ToolRegistry, PermissionLevel
from src.research_agent.research_controller import ResearchController
from src.assignment_agent.assignment_controller import AssignmentController
from src.website_agent.website_controller import WebsiteController
from src.intelligence.decision_engine import HybridDecisionEngine


class TestAutonomousEmployee(unittest.TestCase):
    """
    Validates VoiceMate's Autonomous AI Employee capabilities.
    """

    def setUp(self):
        self.engine = HybridDecisionEngine()

    def test_01_task_planner_goal_decomposition(self):
        """Test 1: Autonomous Planner breaks complex goals into sequential PlanSteps."""
        # Assignment Goal
        plan_assign = TaskPlanner.create_plan("assignment.pdf থেকে প্রশ্ন পড়ে সমাধান তৈরি করে docx ফাইলে সেভ করো")
        self.assertEqual(plan_assign.domain, TaskDomain.ASSIGNMENT_DOCUMENT)
        self.assertGreaterEqual(len(plan_assign.steps), 4)
        self.assertEqual(plan_assign.steps[0].assigned_agent, "document_agent")
        self.assertEqual(plan_assign.steps[2].assigned_agent, "assignment_agent")

        # Website Goal
        plan_web = TaskPlanner.create_plan("আমাকে একটা Hospital Management Website বানিয়ে দাও। এতে Admin ও Doctor Dashboard থাকবে")
        self.assertEqual(plan_web.domain, TaskDomain.WEBSITE_DEVELOPMENT)
        self.assertGreaterEqual(len(plan_web.steps), 4)
        self.assertEqual(plan_web.steps[0].assigned_agent, "website_agent")

        # Deep Research Goal
        plan_res = TaskPlanner.create_plan("কোয়ান্টাম কম্পিউটিং কী? ইন্টারনেটে রিসার্চ রিপোর্ট দাও")
        self.assertEqual(plan_res.domain, TaskDomain.INTERNET_RESEARCH)
        self.assertGreaterEqual(len(plan_res.steps), 3)

        print("\n[Test 1 PASS] Task Planner Goal Decomposition verified across Assignment, Web, and Research domains.")

    def test_02_deep_internet_research_with_citations(self):
        """Test 2: Internet Research Agent synthesizes report with verified sources and citations."""
        res = ResearchController.conduct_deep_research("Artificial Intelligence & Agentic Workflows")
        self.assertTrue(res["success"])
        report = res["report"]
        self.assertIn("summary", report)
        self.assertGreater(len(report["sources"]), 0)
        self.assertGreater(len(report["key_facts"]), 0)
        for s in report["sources"]:
            self.assertTrue(s["url"].startswith("http"))
        print(f"\n[Test 2 PASS] Deep Internet Research -> Topic: '{res['topic']}', Citations: {len(report['sources'])} sources.")

    def test_03_assignment_solver_and_pure_docx_export(self):
        """Test 3: Assignment Agent parses questions, researches solutions, and exports genuine .docx file."""
        res = AssignmentController.execute_assignment_workflow("test_assignment.md")
        self.assertTrue(res["success"])
        self.assertGreater(res["parsed_assignment"]["total_questions"], 0)
        exported = res["exported_files"]

        # Check DOCX file
        docx_path = Path(exported["docx_path"])
        self.assertTrue(docx_path.exists())
        self.assertGreater(docx_path.stat().st_size, 500)  # Genuine non-empty zip/OpenXML archive

        # Check Markdown file
        md_path = Path(exported["md_path"])
        self.assertTrue(md_path.exists())
        self.assertGreater(md_path.stat().st_size, 200)

        print(f"\n[Test 3 PASS] Assignment Agent -> Questions: {res['parsed_assignment']['total_questions']}, DOCX: {docx_path.name} ({docx_path.stat().st_size} bytes).")

    def test_04_website_scaffolding_and_local_server(self):
        """Test 4: Website Agent scaffolds Hospital Management project and verifies local preview server."""
        prompt = "Hospital Management Website with Admin, Doctor, and Patient Dashboards"
        res = WebsiteController.build_and_deploy_website(prompt)

        self.assertTrue(res["success"])
        project_dir = Path(res["project_dir"])
        self.assertTrue(project_dir.exists())

        # Verify generated files
        for f in ["index.html", "dashboard.html", "styles.css", "app.js", "README.md"]:
            f_path = project_dir / f
            self.assertTrue(f_path.exists(), f"Missing file: {f}")
            self.assertGreater(f_path.stat().st_size, 50)

        # Verify live preview URL
        self.assertTrue(res["live_url"].startswith("http://localhost:"))
        self.assertTrue(res["is_verified"])
        print(f"\n[Test 4 PASS] Website Agent -> Project: '{res['project_name']}', Live URL: {res['live_url']}")

    def test_05_tool_registry_and_permission_levels(self):
        """Test 5: Central Tool Registry accurately validates safe tools vs approval-gated actions."""
        # Safe tool
        safe_perm = ToolRegistry.get_permission_level("conduct_deep_research")
        self.assertEqual(safe_perm, PermissionLevel.SAFE)

        # Dangerous tool requiring approval
        risky_perm = ToolRegistry.get_permission_level("delete_file")
        self.assertEqual(risky_perm, PermissionLevel.REQUIRES_APPROVAL)

        # Execute safe tool via registry
        success, data, msg = ToolRegistry.execute_tool(
            agent_name="research_agent",
            tool_name="conduct_deep_research",
            parameters={"topic": "Quantum Computing"}
        )
        self.assertTrue(success)
        self.assertIsNotNone(data)
        print("\n[Test 5 PASS] Tool Registry & Permission Gatekeeper verified.")

    def test_06_end_to_end_autonomous_decision_engine_pipeline(self):
        """Test 6: Natural language commands trigger the Autonomous Plan & Execution Pipeline."""
        # Natural language command to develop a website
        cmd = "আমাকে একটা Hospital Management Website বানিয়ে দাও। এতে Admin ও Doctor Dashboard থাকবে"
        intent_res, response = self.engine.process_query(cmd)

        self.assertEqual(intent_res.source, "task_planner")
        self.assertIn("live_url", intent_res.parameters["plan"]["context_data"])
        self.assertIn("ওয়েবসাইট সফলভাবে তৈরি", response)

        # Natural language command to solve assignment
        cmd_assign = "অ্যাসাইনমেন্ট সলভ করে docx ফাইলে সেভ করো"
        intent_res_a, response_a = self.engine.process_query(cmd_assign)

        self.assertEqual(intent_res_a.source, "task_planner")
        self.assertIn("docx_path", intent_res_a.parameters["plan"]["context_data"]["exported_files"])
        self.assertIn("অ্যাসাইনমেন্টের সমাধান", response_a)

        print("\n[Test 6 PASS] End-to-End Autonomous AI Employee Pipeline verified via natural voice/text commands.")


if __name__ == "__main__":
    unittest.main()
