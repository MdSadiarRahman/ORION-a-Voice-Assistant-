import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.website_agent.website_controller import WebsiteController


class TestWebsiteAgent(unittest.TestCase):
    def test_builds_and_verifies_a_local_prototype(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "projects"
            with patch.object(WebsiteController, "WORKSPACE_DIR", workspace):
                result = WebsiteController.build_and_deploy_website(
                    "Clinic dashboard <script>alert('x')</script>"
                )
                project = Path(result["project_dir"])
                try:
                    self.assertTrue(result["success"])
                    self.assertTrue(result["is_verified"])
                    self.assertTrue(result["live_url"].startswith("http://127.0.0.1:"))
                    self.assertEqual(
                        {path.name for path in project.iterdir()},
                        {"index.html", "dashboard.html", "styles.css", "app.js", "README.md"},
                    )
                    html = (project / "index.html").read_text(encoding="utf-8")
                    self.assertIn("&lt;script&gt;", html)
                    self.assertNotIn("<script>alert('x')</script>", html)
                finally:
                    WebsiteController.stop_local_server(str(project))

    def test_preview_rejects_directories_outside_generated_workspace(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "projects"
            outside = Path(temp_dir) / "outside"
            outside.mkdir()
            with patch.object(WebsiteController, "WORKSPACE_DIR", workspace):
                with self.assertRaises(ValueError):
                    WebsiteController.launch_local_server(str(outside))


if __name__ == "__main__":
    unittest.main()
