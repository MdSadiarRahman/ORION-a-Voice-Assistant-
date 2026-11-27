"""Generate static website projects and serve them on localhost for preview."""

import html
import re
import socket
import threading
import urllib.request
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from config import BASE_DIR


class WebsiteController:
    WORKSPACE_DIR = BASE_DIR / "workspace" / "projects"
    _active_servers: dict[tuple[str, int], ThreadingHTTPServer] = {}
    _server_lock = threading.Lock()

    @classmethod
    def _infer_project_slug(cls, prompt: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9\s-]", " ", prompt.lower())
        words = re.sub(r"\s+", " ", normalized).strip().split()
        if "hospital" in words or "হাসপাতাল" in prompt:
            return "hospital-management-system"
        if any(word in words for word in ("ecommerce", "store", "shop")):
            return "ecommerce-store"
        if "portfolio" in words:
            return "developer-portfolio"
        return "-".join(words[:4]) or "custom-webapp"

    @classmethod
    def scaffold_website(cls, requirements_prompt: str) -> dict[str, Any]:
        cls.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        slug = cls._infer_project_slug(requirements_prompt)
        project_dir = (cls.WORKSPACE_DIR / slug).resolve()
        if cls.WORKSPACE_DIR.resolve() not in project_dir.parents:
            raise ValueError("Generated project path must stay inside the website workspace.")
        project_dir.mkdir(parents=True, exist_ok=True)

        title = html.escape(slug.replace("-", " ").title())
        requirements = html.escape(requirements_prompt.strip())
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        (project_dir / "index.html").write_text(
            f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><link rel="stylesheet" href="styles.css"></head>
<body>
<header><a class="brand" href="/"> {title}</a><nav><a href="#services">Services</a><a href="dashboard.html">Dashboard</a></nav></header>
<main><section class="hero"><p class="eyebrow">Local preview</p><h1>{title}</h1>
<p>{requirements}</p><a class="button" href="dashboard.html">Open dashboard</a></section>
<section id="services" class="cards"><article><h2>Overview</h2><p>A responsive starter page generated for your project.</p></article>
<article><h2>Next steps</h2><p>Connect your own data source and configure authentication before production use.</p></article></section></main>
<footer>Generated locally by VoiceMate · {created_at}</footer><script src="app.js"></script></body></html>
""",
            encoding="utf-8",
        )
        (project_dir / "dashboard.html").write_text(
            f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} Dashboard</title><link rel="stylesheet" href="styles.css"></head>
<body><header><a class="brand" href="index.html">{title}</a><nav><a href="index.html">Home</a></nav></header>
<main><section class="hero"><p class="eyebrow">Starter dashboard</p><h1>Project dashboard</h1>
<p>This is a local UI prototype. No real accounts, patient records, or backend services are connected.</p></section>
<section class="cards"><article><h2>Admin</h2><p>Manage project settings and access.</p></article>
<article><h2>Team</h2><p>Add your own role-specific workflows.</p></article>
<article><h2>Activity</h2><p>Connect an API before using real data.</p></article></section>
<form id="note-form"><label for="note">Local demo note</label><input id="note" maxlength="160" required>
<button class="button" type="submit">Save note</button></form><p id="note-status" aria-live="polite"></p></main>
<script src="app.js"></script></body></html>
""",
            encoding="utf-8",
        )
        (project_dir / "styles.css").write_text(
            """*{box-sizing:border-box}body{margin:0;font:16px/1.6 system-ui,sans-serif;color:#172033;background:#f4f7fb}
header,footer{padding:1rem max(5vw,1.25rem);background:#fff}header{display:flex;justify-content:space-between;align-items:center}
nav{display:flex;gap:1rem}a{color:#1457a6}.brand{font-weight:700;text-decoration:none}.hero,.cards,form{max-width:980px;margin:2rem auto;padding:1.5rem}
.hero{background:#e5efff;border-radius:1rem}.eyebrow{color:#1457a6;text-transform:uppercase;letter-spacing:.08em}
h1{font-size:clamp(2rem,5vw,3.5rem);line-height:1.1}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1rem}
article,form{background:#fff;border-radius:.75rem;padding:1.25rem;box-shadow:0 4px 18px #17203312}.button,button{display:inline-block;background:#1457a6;color:#fff;border:0;border-radius:.5rem;padding:.7rem 1rem;text-decoration:none;cursor:pointer}
input{display:block;width:100%;padding:.7rem;margin:.5rem 0 1rem;border:1px solid #aeb9ca;border-radius:.4rem}footer{margin-top:3rem}
""",
            encoding="utf-8",
        )
        (project_dir / "app.js").write_text(
            """const form = document.querySelector("#note-form");
if (form) {
  const field = document.querySelector("#note");
  const status = document.querySelector("#note-status");
  field.value = localStorage.getItem("voicemate-demo-note") || "";
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    localStorage.setItem("voicemate-demo-note", field.value);
    status.textContent = "Saved in this browser only.";
  });
}
""",
            encoding="utf-8",
        )
        readme = (
            f"# {slug.replace('-', ' ').title()}\n\n"
            "A static website prototype generated locally by VoiceMate.\n\n"
            f"- Requirements: {requirements_prompt.strip()}\n"
            "- Files: `index.html`, `dashboard.html`, `styles.css`, `app.js`\n"
            "- The preview is local only; it has no authentication or production backend.\n"
            f"- Generated: {created_at}\n"
        )
        (project_dir / "README.md").write_text(readme, encoding="utf-8")
        return {
            "slug": slug,
            "project_dir": str(project_dir),
            "files": ["index.html", "dashboard.html", "styles.css", "app.js", "README.md"],
        }

    @classmethod
    def _find_free_port(cls, start: int = 8090) -> int:
        for port in range(start, start + 50):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                try:
                    listener.bind(("127.0.0.1", port))
                    return port
                except OSError:
                    continue
        raise OSError("No available localhost port in the configured range.")

    @classmethod
    def launch_local_server(cls, project_dir: str, port: Optional[int] = None) -> tuple[int, str]:
        root = Path(project_dir).resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Website project directory does not exist: {root}")
        workspace = cls.WORKSPACE_DIR.resolve()
        if workspace not in root.parents:
            raise ValueError("Website previews are limited to generated workspace projects.")
        with cls._server_lock:
            for active_root, active_port in cls._active_servers:
                if active_root == str(root):
                    return active_port, f"http://127.0.0.1:{active_port}/index.html"

        preferred_port = port or 8090
        try:
            server = cls._create_server(root, preferred_port)
            actual_port = preferred_port
        except OSError:
            actual_port = cls._find_free_port(preferred_port + 1)
            server = cls._create_server(root, actual_port)

        key = (str(root), actual_port)
        with cls._server_lock:
            existing = cls._active_servers.get(key)
            if existing:
                server.server_close()
            else:
                cls._active_servers[key] = server
                threading.Thread(
                    target=server.serve_forever,
                    name=f"website-preview-{actual_port}",
                    daemon=True,
                ).start()

        return actual_port, f"http://127.0.0.1:{actual_port}/index.html"

    @classmethod
    def stop_local_server(cls, project_dir: str) -> bool:
        root = str(Path(project_dir).resolve())
        with cls._server_lock:
            servers = [
                (key, server)
                for key, server in cls._active_servers.items()
                if key[0] == root
            ]
            for key, _ in servers:
                del cls._active_servers[key]
        for _, server in servers:
            server.shutdown()
            server.server_close()
        return bool(servers)

    @staticmethod
    def _create_server(root: Path, port: int) -> ThreadingHTTPServer:
        class QuietHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, directory=str(root), **kwargs)

            def log_message(self, format: str, *args: Any) -> None:
                return

        class LocalServer(ThreadingHTTPServer):
            daemon_threads = True
            allow_reuse_address = True

        return LocalServer(("127.0.0.1", port), QuietHandler)

    @staticmethod
    def verify_server(url: str) -> tuple[bool, str]:
        parsed = urlparse(url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
            return False, "Preview verification only permits localhost URLs."
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True, "ওয়েবসাইটের localhost preview সফলভাবে যাচাই হয়েছে।"
                return False, f"Preview server returned HTTP {response.status}."
        except (OSError, TimeoutError) as exc:
            return False, f"ওয়েবসাইট preview যাচাই করা যায়নি: {exc}"

    @classmethod
    def build_and_deploy_website(cls, requirements_prompt: str) -> dict[str, Any]:
        scaffold = cls.scaffold_website(requirements_prompt)
        port, live_url = cls.launch_local_server(scaffold["project_dir"])
        verified, message = cls.verify_server(live_url)
        return {
            "success": verified,
            "project_name": scaffold["slug"],
            "project_dir": scaffold["project_dir"],
            "files": scaffold["files"],
            "port": port,
            "live_url": live_url,
            "is_verified": verified,
            "verification_message": message,
            "voice_summary": (
                f"ওয়েবসাইট প্রোটোটাইপ তৈরি হয়েছে। লোকাল preview: {live_url}"
                if verified
                else f"ওয়েবসাইট ফাইল তৈরি হয়েছে, তবে preview যাচাই ব্যর্থ: {message}"
            ),
        }
