from src.intelligence.intent_router import IntentRouter
from src.intelligence.tool_registry import ToolRegistry

ir = IntentRouter()
tr = ToolRegistry()

tests = [
    'chrome kholo',
    'open chrome',
    'vs code open',
    'notepad open koro',
    'kemon acho',
    'bangladesh er rajdhani ki',
]
for t in tests:
    r = ir.route(t)
    print(f"[{t}] -> intent={r.intent} conf={r.confidence} params={r.parameters}")
    if r.confidence >= 0.85 and tr.has_tool(r.intent):
        res = tr.execute(r.intent, **r.parameters)
        print(f"   tool_ok={res.get('ok')} reply={res.get('reply')}")
