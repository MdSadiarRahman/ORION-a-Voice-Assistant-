"""
ToolRegistry for VoiceMate Advanced Hybrid Architecture.
Registers and executes Python tools safely (no eval/exec) and returns
structured JSON-serializable schemas.
"""
import ast
import operator
import os
import re
import shutil
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


def _extract_file_search_terms(query: str) -> str:
    clean = (query or "").strip()
    noise = [
        "আমার", "পিসিতে", "ল্যাপটপে", "থাকা", "ফাইলটা", "ফাইলটি", "ফাইল", "ডকুমেন্ট",
        "খুঁজে দাও", "খুঁজো", "খুঁজে বের করো", "খুলো", "খোলো", "ওপেন করো", "পড়ো", "পড়ো",
        "find my", "find file", "search file", "open file", "read file", "read document", "read pdf",
        "please", "dao", "koro", "the", "my",
    ]
    for n in noise:
        clean = re.sub(rf"(?i)(^|[^\w\u0980-\u09FF]){re.escape(n)}($|[^\w\u0980-\u09FF])", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


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
        self.register("GET_WEATHER", self._tool_get_weather)
        self.register("SEARCH_LOCAL_FILE", self._tool_search_local_file)
        self.register("OPEN_FILE", self._tool_open_file)
        self.register("READ_DOCUMENT", self._tool_read_document)
        self.register("WEB_SEARCH", self._tool_web_search)

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
    def _tool_get_weather(query: str = "", **kwargs: Any) -> Dict[str, Any]:
        from src.helpers.web_research_helper import WebResearchHelper
        reply = WebResearchHelper.get_weather(query)
        return {"ok": True, "intent": "GET_WEATHER", "reply": reply}

    @staticmethod
    def _tool_search_local_file(query: str = "", **kwargs: Any) -> Dict[str, Any]:
        from config import DOCS_DIR
        from src.document_intelligence.file_search import FileSearchEngine
        eng = FileSearchEngine()
        if DOCS_DIR.exists() and DOCS_DIR not in eng.authorized_roots:
            eng.authorized_roots.append(DOCS_DIR)

        cleaned = _extract_file_search_terms(query)
        exts = None
        if "pdf" in query.lower() or "পিডিএফ" in query.lower():
            exts = {".pdf"}
            cleaned = re.sub(r"(?i)\b(pdf|পিডিএফ)\b", "", cleaned).strip()

        results = eng.search(cleaned or "", extensions=exts, search_content=bool(cleaned), max_results=5)
        if not results and cleaned:
            results = eng.search("", extensions=exts, max_results=5)

        if results:
            top_list = "\n".join(f"• {r.filename} ({r.folder})" for r in results[:3])
            spoken = f"আপনার পিসিতে {len(results)}টি ফাইল পাওয়া গেছে:\n{top_list}"
            return {
                "ok": True,
                "intent": "SEARCH_LOCAL_FILE",
                "files": [str(r.path) for r in results],
                "reply": spoken,
            }
        return {
            "ok": True,
            "intent": "SEARCH_LOCAL_FILE",
            "files": [],
            "reply": "দুঃখিত, আপনার পিসিতে অনুরোধ করা ফাইলটি খুঁজে পাওয়া যায়নি।",
        }

    @staticmethod
    def _tool_open_file(query: str = "", **kwargs: Any) -> Dict[str, Any]:
        res = ToolRegistry._tool_search_local_file(query=query)
        files = res.get("files", [])
        if not files:
            return {"ok": True, "intent": "OPEN_FILE", "reply": "দুঃখিত, খোলার জন্য ফাইলটি খুঁজে পাওয়া যায়নি।"}
        target = files[0]
        try:
            os.startfile(target)
            return {
                "ok": True,
                "intent": "OPEN_FILE",
                "file": target,
                "reply": f"ফাইল খোলা হচ্ছে: {os.path.basename(target)}",
            }
        except Exception as e:
            return {"ok": False, "intent": "OPEN_FILE", "error": str(e), "reply": f"ফাইলটি খোলা যায়নি: {e}"}

    @staticmethod
    def _tool_read_document(query: str = "", **kwargs: Any) -> Dict[str, Any]:
        from src.document_agent.document_task_runner import DocumentTaskRunner
        from src.document_agent.pymupdf_reader import PyMuPDFReader
        from src.document_agent.document_fallback import DocumentFallbackReader

        cleaned = _extract_file_search_terms(query) or query
        path = DocumentTaskRunner.resolve_document_path(cleaned)
        if not path:
            return {"ok": True, "intent": "READ_DOCUMENT", "reply": f"দুঃখিত, '{cleaned}' নামে কোনো ডকুমেন্ট পাওয়া যায়নি।"}

        if PyMuPDFReader.is_available() and path.suffix.lower() in [".pdf", ".xps", ".epub"]:
            summary = PyMuPDFReader.get_document_summary_for_voice(str(path))
        else:
            fallback = DocumentFallbackReader.read_text_document(str(path))
            summary = fallback.get("summary", "ডকুমেন্ট পড়া সম্পন্ন হয়েছে।")
        return {"ok": True, "intent": "READ_DOCUMENT", "file": str(path), "reply": summary}

    @staticmethod
    def _tool_web_search(query: str = "", **kwargs: Any) -> Dict[str, Any]:
        from src.helpers.web_research_helper import WebResearchHelper
        from src.helpers.search_helper import SearchHelper
        reply = WebResearchHelper.search_and_answer(query)
        if "সরাসরি কোনো সারসংক্ষেপ পাওয়া যায়নি" in reply:
            SearchHelper.search_in_google(query)
            return {"ok": True, "intent": "WEB_SEARCH", "reply": f"গুগলে {query} সার্চ করা হচ্ছে"}
        return {"ok": True, "intent": "WEB_SEARCH", "reply": reply}

    @staticmethod
    def _tool_open_application(app_name: str = "", **kwargs: Any) -> Dict[str, Any]:
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
        hardcoded_paths = {
            "code": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "Code.exe"),
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "msedge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "winword": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        }
        name_clean = app_name.lower().strip()
        cmd = app_map.get(name_clean, name_clean)
        if not cmd:
            return {"ok": False, "intent": "OPEN_APPLICATION", "error": "Empty app_name", "reply": "কোন অ্যাপ খুলতে হবে তা বলেননি।"}

        if cmd.startswith("ms-"):
            subprocess.Popen(["cmd", "/c", "start", "", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            return {"ok": True, "intent": "OPEN_APPLICATION", "app_name": app_name, "reply": f"{app_name} খোলা হচ্ছে।"}

        full_path_hc = hardcoded_paths.get(cmd)
        if full_path_hc and os.path.isfile(full_path_hc):
            subprocess.Popen([full_path_hc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "intent": "OPEN_APPLICATION", "app_name": app_name, "command": full_path_hc, "reply": f"{app_name} চালু করা হচ্ছে।"}

        if shutil.which(cmd):
            subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "intent": "OPEN_APPLICATION", "app_name": app_name, "command": cmd, "reply": f"{app_name} চালু করা হচ্ছে।"}

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

        subprocess.Popen(f'start "" "{cmd}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "intent": "OPEN_APPLICATION", "app_name": app_name, "command": cmd, "reply": f"{app_name} চালু করা হচ্ছে।"}
