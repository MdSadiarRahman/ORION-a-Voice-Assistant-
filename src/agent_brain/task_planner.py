"""
VoiceMate Agent Brain - Autonomous Task Planner & Multi-Agent Orchestrator.
Transforms VoiceMate into an autonomous Personal AI Employee by breaking high-level
user goals into sequential executable steps, passing data between specialized agents,
verifying step outcomes, and enforcing human-in-the-loop approvals for sensitive actions.
"""
import os
import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger("VoiceMate.AgentBrain.TaskPlanner")


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


class TaskDomain(Enum):
    MEDIA_YOUTUBE = "media_youtube"
    PRODUCT_RESEARCH = "product_research"
    INTERNET_RESEARCH = "internet_research"
    ASSIGNMENT_DOCUMENT = "assignment_document"
    WEBSITE_DEVELOPMENT = "website_development"
    WINDOWS_AUTOMATION = "windows_automation"
    GENERAL = "general"


@dataclass
class PlanStep:
    """
    Represents an individual executable step in an autonomous multi-agent plan.
    """
    step_id: int
    title: str
    assigned_agent: str  # 'research_agent', 'document_agent', 'coding_agent', etc.
    tool_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    requires_approval: bool = False
    approval_prompt: Optional[str] = None
    is_verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "assigned_agent": self.assigned_agent,
            "tool_name": self.tool_name,
            "status": self.status.value,
            "requires_approval": self.requires_approval,
            "is_verified": self.is_verified,
            "error": self.error
        }


@dataclass
class ExecutionPlan:
    """
    Complete stateful multi-step execution plan for an autonomous task.
    """
    plan_id: str
    goal: str
    domain: TaskDomain
    steps: List[PlanStep] = field(default_factory=list)
    current_step_index: int = 0
    context_data: Dict[str, Any] = field(default_factory=dict)
    is_completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    final_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "domain": self.domain.value,
            "total_steps": len(self.steps),
            "current_step": self.current_step_index,
            "is_completed": self.is_completed,
            "context_data": self.context_data,
            "steps": [s.to_dict() for s in self.steps],
            "final_summary": self.final_summary
        }


class TaskPlanner:
    """
    Autonomous Planner that decomposes complex human goals into structured,
    executable multi-agent workflows.
    """

    @classmethod
    def create_plan(cls, user_goal: str) -> ExecutionPlan:
        """
        Analyzes the user's high-level goal and constructs an executable step-by-step plan.
        """
        goal_clean = user_goal.strip()
        lower_goal = goal_clean.lower()
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 1. ASSIGNMENT & PDF WORKFLOW
        # e.g.: "assignment.pdf থেকে প্রশ্ন পড়ে সমাধান তৈরি করে docx ফাইলে সেভ করো"
        if any(w in lower_goal for w in ["assignment", "অ্যাসাইনমেন্ট", "প্রশ্ন", "সমাধান"]) and any(w in lower_goal for w in ["pdf", "docx", "ডকুমেন্ট", "সলভ", "solve", "ফাইল"]):
            # Extract filename if specified
            file_match = re.search(r'([\w\s.-]+\.(?:pdf|docx|txt|md))', goal_clean, re.IGNORECASE)
            target_file = file_match.group(1).strip() if file_match else "assignment.pdf"

            steps = [
                PlanStep(
                    step_id=1,
                    title=f"Extract questions and topic from {target_file}",
                    assigned_agent="document_agent",
                    tool_name="extract_assignment_questions",
                    parameters={"filename": target_file}
                ),
                PlanStep(
                    step_id=2,
                    title="Research academic concepts and citations on the web",
                    assigned_agent="research_agent",
                    tool_name="research_academic_sources",
                    parameters={"use_step_output": 1}
                ),
                PlanStep(
                    step_id=3,
                    title="Draft step-by-step educational solutions with explanations",
                    assigned_agent="assignment_agent",
                    tool_name="draft_assignment_solutions",
                    parameters={"use_step_output": [1, 2]}
                ),
                PlanStep(
                    step_id=4,
                    title="Generate and export formatted DOCX/Markdown solution document",
                    assigned_agent="document_agent",
                    tool_name="export_solution_document",
                    parameters={"output_format": "docx"}
                ),
                PlanStep(
                    step_id=5,
                    title="Verify document integrity and present summary to user",
                    assigned_agent="verifier_agent",
                    tool_name="verify_assignment_output",
                    parameters={"use_step_output": 4}
                )
            ]
            return ExecutionPlan(plan_id=plan_id, goal=goal_clean, domain=TaskDomain.ASSIGNMENT_DOCUMENT, steps=steps)

        # 2. WEBSITE DEVELOPMENT WORKFLOW
        # e.g.: "আমাকে একটা Hospital Management Website বানিয়ে দাও। এতে Admin, Doctor, Patient Dashboard থাকবে"
        if any(w in lower_goal for w in ["website", "ওয়েবসাইট", "web app", "ওয়েব"]) and any(w in lower_goal for w in ["বানিয়ে", "তৈরি", "build", "create", "make", "ডেভেলপ"]):
            steps = [
                PlanStep(
                    step_id=1,
                    title="Analyze user requirements and design website architecture",
                    assigned_agent="website_agent",
                    tool_name="plan_website_architecture",
                    parameters={"requirements": goal_clean}
                ),
                PlanStep(
                    step_id=2,
                    title="Scaffold responsive frontend pages (HTML, CSS/Tailwind, JavaScript)",
                    assigned_agent="coding_agent",
                    tool_name="scaffold_website_project",
                    parameters={"use_step_output": 1}
                ),
                PlanStep(
                    step_id=3,
                    title="Implement interactive dashboards, forms, and client state storage",
                    assigned_agent="coding_agent",
                    tool_name="implement_dashboard_features",
                    parameters={"use_step_output": 2}
                ),
                PlanStep(
                    step_id=4,
                    title="Launch local web server and verify pages load without errors",
                    assigned_agent="system_agent",
                    tool_name="launch_and_verify_web_server",
                    parameters={"port": 8090}
                ),
                PlanStep(
                    step_id=5,
                    title="Generate project documentation and present live preview link to user",
                    assigned_agent="verifier_agent",
                    tool_name="verify_website_deployment",
                    parameters={"use_step_output": [2, 4]}
                )
            ]
            return ExecutionPlan(plan_id=plan_id, goal=goal_clean, domain=TaskDomain.WEBSITE_DEVELOPMENT, steps=steps)

        # 3. PRODUCT & PRICE RESEARCH WORKFLOW
        # e.g.: "Sony WH-CH720N এর দাম কত? বিভিন্ন দোকানের দাম ও স্পেক্স তুলনা করে বলো"
        if any(w in lower_goal for w in ["দাম", "price", "দোকান", "তুলনা", "compare", "মার্কেট", "best", "cheapest"]) and any(w in lower_goal for w in ["laptop", "phone", "headphone", "sony", "samsung", "hp", "পণ্য", "প্রোডাক্ট"]):
            steps = [
                PlanStep(
                    step_id=1,
                    title="Extract product name, model, and budget specifications",
                    assigned_agent="product_agent",
                    tool_name="extract_product_parameters",
                    parameters={"query": goal_clean}
                ),
                PlanStep(
                    step_id=2,
                    title="Scrape prices from verified Bangladeshi retailers (Star Tech, Ryans, Daraz)",
                    assigned_agent="product_agent",
                    tool_name="scrape_retailer_prices",
                    parameters={"use_step_output": 1}
                ),
                PlanStep(
                    step_id=3,
                    title="Compare model listings, calculate price differences, and find best deal",
                    assigned_agent="product_agent",
                    tool_name="compare_product_listings",
                    parameters={"use_step_output": 2}
                ),
                PlanStep(
                    step_id=4,
                    title="Verify store URLs, check availability, and format voice summary",
                    assigned_agent="verifier_agent",
                    tool_name="verify_and_summarize_product",
                    parameters={"use_step_output": 3}
                )
            ]
            return ExecutionPlan(plan_id=plan_id, goal=goal_clean, domain=TaskDomain.PRODUCT_RESEARCH, steps=steps)

        # 4. DEEP INTERNET RESEARCH WORKFLOW
        # e.g.: "কোয়ান্টাম কম্পিউটিং কী? ইন্টারনেটে রিসার্চ করে সোর্সসহ বিস্তারিত রিপোর্ট দাও"
        if any(w in lower_goal for w in ["রিসার্চ", "research", "খুঁজে বের করো", "বিস্তারিত", "তথ্য দাও", "report"]) and not any(w in lower_goal for w in ["গান", "ভিডিও", "play"]):
            steps = [
                PlanStep(
                    step_id=1,
                    title="Formulate targeted web search queries across authoritative sources",
                    assigned_agent="research_agent",
                    tool_name="formulate_search_queries",
                    parameters={"topic": goal_clean}
                ),
                PlanStep(
                    step_id=2,
                    title="Fetch and scrape content from top reliable web destinations",
                    assigned_agent="research_agent",
                    tool_name="fetch_multi_source_content",
                    parameters={"use_step_output": 1}
                ),
                PlanStep(
                    step_id=3,
                    title="Cross-verify facts and synthesize comprehensive brief with citations",
                    assigned_agent="research_agent",
                    tool_name="synthesize_research_brief",
                    parameters={"use_step_output": 2}
                ),
                PlanStep(
                    step_id=4,
                    title="Verify citation links and present formatted research report to user",
                    assigned_agent="verifier_agent",
                    tool_name="verify_research_report",
                    parameters={"use_step_output": 3}
                )
            ]
            return ExecutionPlan(plan_id=plan_id, goal=goal_clean, domain=TaskDomain.INTERNET_RESEARCH, steps=steps)

        # 5. GENERAL WORKFLOW (Single-phase execution)
        steps = [
            PlanStep(
                step_id=1,
                title="Execute requested desktop task",
                assigned_agent="general_agent",
                tool_name="execute_general_command",
                parameters={"command": goal_clean}
            )
        ]
        return ExecutionPlan(plan_id=plan_id, goal=goal_clean, domain=TaskDomain.GENERAL, steps=steps)

    @classmethod
    def execute_plan(
        cls,
        plan: ExecutionPlan,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> ExecutionPlan:
        """
        Executes a planned workflow sequentially, passing data between agents,
        and stops dependent work when a step fails.
        """
        from src.agent_brain.tool_registry import ToolRegistry, PermissionLevel

        logger.info(f"TaskPlanner executing plan: {plan.plan_id} (Total steps: {len(plan.steps)})")

        for idx, step in enumerate(plan.steps):
            plan.current_step_index = idx + 1
            step.status = StepStatus.RUNNING
            if on_progress:
                on_progress(f"ধাপ {step.step_id}/{len(plan.steps)}: {step.title}")

            perm = ToolRegistry.get_permission_level(step.tool_name)
            if perm == PermissionLevel.REQUIRES_APPROVAL and not plan.context_data.get("user_confirmed", False):
                step.status = StepStatus.WAITING_APPROVAL
                step.approval_prompt = f"গুরুত্বপূর্ণ পদক্ষেপ: '{step.title}' সম্পন্ন করতে আপনার অনুমতি প্রয়োজন। সম্মতি দিচ্ছেন কি?"
                return plan

            # Resolve parameters using previous step outputs if specified
            call_params = dict(step.parameters)
            if "use_step_output" in call_params:
                call_params.update(plan.context_data)

            # Dispatch via ToolRegistry
            success, result_data, msg = ToolRegistry.execute_tool(
                agent_name=step.assigned_agent,
                tool_name=step.tool_name,
                parameters=call_params
            )

            if success:
                step.status = StepStatus.COMPLETED
                step.result = result_data
                step.is_verified = True
                if isinstance(result_data, dict):
                    plan.context_data.update(result_data)
                elif result_data is not None:
                    plan.context_data[f"step_{step.step_id}_output"] = result_data
            else:
                step.status = StepStatus.FAILED
                step.error = msg
                logger.error(f"Step {step.step_id} failed: {msg}")
                for later_step in plan.steps[idx + 1:]:
                    later_step.status = StepStatus.SKIPPED
                    later_step.error = f"আগের ধাপ {step.step_id} ব্যর্থ হওয়ায় চালানো হয়নি।"
                plan.is_completed = False
                plan.final_summary = f"ধাপ {step.step_id} ব্যর্থ হয়েছে: {msg}"
                return plan

        plan.is_completed = bool(plan.steps) and all(
            step.status == StepStatus.COMPLETED for step in plan.steps
        )

        # Build final spoken and text summary
        if plan.domain == TaskDomain.ASSIGNMENT_DOCUMENT:
            exported = plan.context_data.get("exported_files", {})
            docx_p = exported.get("docx_path", "documents/solutions/assignment_solution.docx")
            plan.final_summary = f"অ্যাসাইনমেন্টের সমাধান সফলভাবে তৈরি ও সংরক্ষণ করা হয়েছে: {docx_p}।"
        elif plan.domain == TaskDomain.WEBSITE_DEVELOPMENT:
            live_url = plan.context_data.get("live_url", "http://localhost:8090/index.html")
            plan.final_summary = f"ওয়েবসাইট সফলভাবে তৈরি ও রান করা হয়েছে। লাইভ প্রিভিউ: {live_url}।"
        elif plan.domain == TaskDomain.INTERNET_RESEARCH:
            topic = plan.context_data.get("topic", plan.goal)
            plan.final_summary = f"'{topic}'-এর ওপর বিস্তারিত গবেষণামূলক রিপোর্ট তৈরি সম্পন্ন হয়েছে।"
        elif plan.domain == TaskDomain.PRODUCT_RESEARCH:
            plan.final_summary = plan.context_data.get("voice_summary", "প্রোডাক্টের বাজার দর যাচাই সম্পন্ন হয়েছে।")
        else:
            plan.final_summary = "আপনার নির্দেশিত কাজটি সম্পন্ন হয়েছে।"

        return plan
