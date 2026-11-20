"""
OpenHands Agent Canvas Controller for VoiceMate.
Manages OpenHands Agent Canvas background process, Developer Workspace operations,
and ACP event broadcasting.
"""
import socket
import subprocess
import webbrowser
import threading
from pathlib import Path
from typing import Dict, Any, Optional

from config import (
    OPENHANDS_REPO_DIR,
    CANVAS_PORT,
    CANVAS_AUTO_OPEN_BROWSER,
)
from src.canvas_agent.canvas_config import is_node_available, get_node_executable
from src.canvas_agent.canvas_event_stream import CanvasEventStream, EventKind
from src.canvas_agent.canvas_workspace_runner import CanvasWorkspaceRunner
from src.canvas_agent.canvas_fallback import CanvasFallbackAgent


class CanvasController:
    """
    Central Controller for OpenHands Developer Canvas.
    """
    _server_process: Optional[subprocess.Popen] = None
    _lock = threading.Lock()

    @classmethod
    def is_canvas_running(cls) -> bool:
        """Checks if Canvas port is currently accepting connections or process alive."""
        with cls._lock:
            if cls._server_process and cls._server_process.poll() is None:
                return True

        # Check port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                res = s.connect_ex(("127.0.0.1", CANVAS_PORT))
                return res == 0
        except Exception:
            return False

    @classmethod
    def start_canvas_server(cls, auto_open: Optional[bool] = None) -> Dict[str, Any]:
        """
        Boots the OpenHands Agent Canvas server using Node.js and opens the web canvas.
        """
        stream = CanvasEventStream.get_instance()

        if cls.is_canvas_running():
            msg = f"ওপেনহ্যান্ডস ক্যানভাস ইতোমধ্যে চালু রয়েছে (http://localhost:{CANVAS_PORT})।"
            stream.emit(EventKind.STATUS, msg)
            if auto_open if auto_open is not None else CANVAS_AUTO_OPEN_BROWSER:
                webbrowser.open(f"http://localhost:{CANVAS_PORT}")
            return {"success": True, "running": True, "message": msg, "port": CANVAS_PORT}

        bin_script = OPENHANDS_REPO_DIR / "bin" / "agent-canvas.mjs"
        if not bin_script.exists() or not is_node_available():
            # Fallback
            return CanvasFallbackAgent.open_canvas_in_browser()

        stream.emit(EventKind.ACTION, "ওপেনহ্যান্ডস ক্যানভাস সার্ভার চালু করা হচ্ছে...")

        try:
            node_exe = get_node_executable()
            # Start process in background
            proc = subprocess.Popen(
                [node_exe, str(bin_script)],
                cwd=str(OPENHANDS_REPO_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0
            )

            with cls._lock:
                cls._server_process = proc

            url = f"http://localhost:{CANVAS_PORT}"
            msg = f"ওপেনহ্যান্ডস এজেন্ট ক্যানভাস সার্ভার সফলভাবে চালু হয়েছে: {url}"
            stream.emit(EventKind.STATUS, msg, {"url": url, "port": CANVAS_PORT})

            if auto_open if auto_open is not None else CANVAS_AUTO_OPEN_BROWSER:
                # Open browser
                threading.Timer(2.0, lambda: webbrowser.open(url)).start()

            return {
                "success": True,
                "running": True,
                "url": url,
                "port": CANVAS_PORT,
                "message": msg
            }
        except Exception as e:
            err_msg = f"ক্যানভাস সার্ভার চালুকরণে ব্যর্থ: {str(e)}"
            stream.emit(EventKind.OBSERVATION, err_msg)
            return {"success": False, "running": False, "error": str(e), "message": err_msg}

    @classmethod
    def stop_canvas_server(cls) -> Dict[str, Any]:
        """Stops the active canvas server process."""
        with cls._lock:
            if cls._server_process and cls._server_process.poll() is None:
                try:
                    cls._server_process.terminate()
                    cls._server_process = None
                    msg = "ওপেনহ্যান্ডস ক্যানভাস সার্ভার বন্ধ করা হয়েছে।"
                    CanvasEventStream.get_instance().emit(EventKind.STATUS, msg)
                    return {"success": True, "message": msg}
                except Exception as e:
                    return {"success": False, "error": str(e)}

        return {"success": True, "message": "কোনো সক্রিয় ক্যানভাস সার্ভার নেই।"}

    @classmethod
    def audit_code(cls, path: Optional[Path] = None) -> Dict[str, Any]:
        """Runs codebase audit."""
        return CanvasWorkspaceRunner.audit_codebase(path)

    @classmethod
    def get_git_status(cls) -> Dict[str, Any]:
        """Checks git repository status."""
        return CanvasWorkspaceRunner.get_git_status()

    @classmethod
    def get_file_tree(cls) -> Dict[str, Any]:
        """Gets project file tree."""
        return CanvasWorkspaceRunner.get_file_tree()

    @classmethod
    def run_terminal_command(cls, cmd: str) -> Dict[str, Any]:
        """Runs terminal command."""
        return CanvasWorkspaceRunner.execute_terminal_command(cmd)
