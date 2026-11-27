import json, sys, os
# Ensure project root is on sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
from src.assignment_agent.assignment_controller import AssignmentController
# Use default sample assignment (will fallback to sample if not provided)
result = AssignmentController.execute_assignment_workflow('sample_assignment.md')
print(json.dumps(result, ensure_ascii=False, indent=2))
