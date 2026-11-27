import unittest
from unittest.mock import patch

from src.agent_brain.task_planner import ExecutionPlan, PlanStep, StepStatus, TaskDomain, TaskPlanner
from src.agent_brain.tool_registry import ToolRegistry


class TestTaskPlannerFailures(unittest.TestCase):
    @patch.object(
        ToolRegistry,
        "execute_tool",
        return_value=(False, None, "integration unavailable"),
    )
    def test_failed_step_stops_dependent_steps_without_success_claim(self, execute_tool):
        plan = ExecutionPlan(
            plan_id="failure-test",
            goal="test",
            domain=TaskDomain.INTERNET_RESEARCH,
            steps=[
                PlanStep(1, "search", "research_agent", "conduct_deep_research"),
                PlanStep(2, "summarize", "research_agent", "synthesize_research_brief"),
            ],
        )

        result = TaskPlanner.execute_plan(plan)

        self.assertFalse(result.is_completed)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertEqual(result.steps[1].status, StepStatus.SKIPPED)
        self.assertIn("ব্যর্থ", result.final_summary)
        execute_tool.assert_called_once()


if __name__ == "__main__":
    unittest.main()
