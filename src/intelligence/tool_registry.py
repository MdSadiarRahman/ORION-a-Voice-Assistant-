"""
ToolRegistry for VoiceMate Advanced Hybrid Architecture.
Registers and executes Python tools safely (no eval/exec) and returns
structured JSON-serializable schemas.
"""
import ast
import operator
import subprocess
from datetime import datetime
from typing import Any, Callable, Dict


_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval_ast(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval_ast(node.left), _safe_eval_ast(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval_ast(node.operand))
    raise ValueError("Unsupported mathematical expression")


class ToolRegistry:
    """Registry of deterministic Python tools with structured JSON responses."""

    def __init__(self):
        self._tools: Dict[str, Callable[..., Dict[str, Any]]] = {}
        self._register_default_tools()

    def register(self, intent: str, fn: Callable[..., Dict[str, Any]]) -> None:
        self._tools[intent] = fn

    def has_tool(self, intent: str) -> bool:
        return intent in self._tools

    def execute(self, intent: str, **kwargs: Any) -> Dict[str, Any]:
        if intent not in self._tools:
            return {"ok": False, "intent": intent, "error": f"No tool registered for {intent}", "reply": ""}
        try:
            return self._tools[intent](**kwargs)
        except Exception as e:
            return {"ok": False, "intent": intent, "error": str(e), "reply": f"টুল চালাতে সমস্যা হয়েছে: {e}"}

    def _register_default_tools(self) -> None:
        self.register("GENERAL_GREETING", self._tool_greeting)
        self.register("GET_CURRENT_TIME", self._tool_current_time)
        self.register("GET_CURRENT_DATE", self._tool_current_date)
        self.register("CALCULATE", self._tool_calculate)
        self.register("OPEN_APPLICATION", self._tool_open_application)

    @staticmethod
    def _tool_greeting(**kwargs: Any) -> Dict[str, Any]:
        return {
            "ok": True,
            "intent": "GENERAL_GREETING",
            "reply": "হ্যালো! আমি ভয়েসমেট। আপনাকে কীভাবে সাহায্য করতে পারি?",
        }

    @staticmethod
    def _tool_current_time(**kwargs: Any) -> Dict[str, Any]:
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        return {
            "ok": True,
            "intent": "GET_CURRENT_TIME",
            "time": time_str,
            "reply": f"এখন সময় {time_str}।",
        }

    @staticmethod
    def _tool_current_date(**kwargs: Any) -> Dict[str, Any]:
        now = datetime.now()
        date_str = now.strftime("%A, %d %B %Y")
        return {
            "ok": True,
            "intent": "GET_CURRENT_DATE",
            "date": date_str,
            "reply": f"আজ {date_str}।",
        }

    @staticmethod
    def _tool_calculate(expression: str = "", **kwargs: Any) -> Dict[str, Any]:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval_ast(tree.body)
        formatted = int(result) if result.is_integer() else round(result, 4)
        return {
            "ok": True,
            "intent": "CALCULATE",
            "expression": expression,
            "result": formatted,
            "reply": f"{expression} এর ফলাফল {formatted}।",
        }

    @staticmethod
    def _tool_open_application(app_name: str = "", **kwargs: Any) -> Dict[str, Any]:
        import shutil, os

        # Canonical name → executable / path resolution
        app_map = {
            "vs code": "code",
            "vscode": "code",
            "code": "code",
            "visual studio code": "code",
            "notepad": "notepad",
            "calculator": "calc",
            "chrome": "chrome",
            "google chrome": "chrome",
            "edge": "msedge",
            "microsoft edge": "msedge",
            "cmd": "cmd",
            "command prompt": "cmd",
            "powershell": "powershell",
            "file explorer": "explorer",
            "explorer": "explorer",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
            "paint": "mspaint",
            "task manager": "taskmgr",
            "settings": "ms-settings:",
        }
        # Hardcoded full-path fallbacks for apps not on PATH
        hardcoded_paths = {
            "code": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "Code.exe"),
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "msedge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "winword": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            "excel":   r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        }
        name_clean = app_name.lower().strip()
        cmd = app_map.get(name_clean, name_clean)
        if not cmd:
            return {"ok": False, "intent": "OPEN_APPLICATION", "error": "Empty app_name", "reply": "কোন অ্যাপ খুলতে হবে তা বলেননি।"}

        # ms-settings URI
        if cmd.startswith("ms-"):
            subprocess.Popen(["cmd", "/c", "start", "", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            return {"ok": True, "intent": "OPEN_APPLICATION", "app_name": app_name, "reply": f"{app_name} খোলা হচ্ছে।"}

        # Check hardcoded paths first (for apps not on PATH like VS Code)
        full_path_hc = hardcoded_paths.get(cmd)
        if full_path_hc and os.path.isfile(full_path_hc):
            subprocess.Popen([full_path_hc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "intent": "OPEN_APPLICATION", "app_name": app_name, "command": full_path_hc, "reply": f"{app_name} চালু করা হচ্ছে।"}

        # If the exe is on PATH, run directly
        if shutil.which(cmd):
            subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "intent": "OPEN_APPLICATION", "app_name": app_name, "command": cmd, "reply": f"{app_name} চালু করা হচ্ছে।"}

        # Check hardcoded paths
        full_path = hardcoded_paths.get(cmd)
        if full_path and os.path.isfile(full_path):
            subprocess.Popen([full_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "intent": "OPEN_APPLICATION", "app_name": app_name, "command": full_path, "reply": f"{app_name} চালু করা হচ্ছে।"}

        # Search common install paths for Windows apps
        search_dirs = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
            os.path.join(os.environ.get("APPDATA", ""), "Local\\Programs"),
        ]
        exe_name = cmd if cmd.endswith(".exe") else cmd + ".exe"
        for d in search_dirs:
            if not d:
                continue
            for root, _, files in os.walk(d):
                if exe_name.lower() in [f.lower() for f in files]:
                    full = os.path.join(root, exe_name)
                    subprocess.Popen([full], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return {"ok": True, "intent": "OPEN_APPLICATION", "app_name": app_name, "command": full, "reply": f"{app_name} চালু করা হচ্ছে।"}

        # Final fallback: Windows START shell
        subprocess.Popen(f'start "" "{cmd}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "intent": "OPEN_APPLICATION", "app_name": app_name, "command": cmd, "reply": f"{app_name} চালু করা হচ্ছে।"}
