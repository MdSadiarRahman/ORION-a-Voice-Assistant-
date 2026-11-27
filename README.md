# VoiceMate - Laptop Voice Assistant Agent (Desktop Edition)
**ভয়েস মেট - ল্যাপটপ ভয়েস অ্যাসিস্ট্যান্ট এজেন্ট**

VoiceMate হলো Windows-এর জন্য বাংলা ও ইংরেজি voice assistant। সক্রিয় voice/text command path-এ এটি শুধু নিচের পাঁচটি কাজের জন্য তৈরি; এর বাইরে কমান্ড দিলে scope-এর সীমা জানায়। Repository-তে থাকা পুরোনো agent/module-গুলো বর্তমান voice route বা UI toolkit দিয়ে চালু হয় না।

---

## 🚀 সক্রিয় সুবিধাসমূহ (Supported Features)

1. **অ্যাপ খোলা:** Windows-এ ইনস্টল করা app খোঁজে; WhatsApp, Gmail, ChatGPT, Messenger, Telegram, VS Code/“Voice Code” ও Antigravity-এর মতো alias সমর্থন করে। স্থানীয় app না মিললে Gmail/ChatGPT/Messenger/Telegram/WhatsApp-এর web version খোলে।
2. **ভয়েস টাইপিং:** *"টাইপিং মোড"* বললে বর্তমান active window-এর focus করা text field-এ কথাগুলো লেখা হয়। টাইপিং মোডে *"টাইপিং বন্ধ"* বললে মোড বন্ধ হয়। কোনো dictated phrase নিজে থেকে message send করে না; পাঠানোর আগে ব্যবহারকারীকে সংশ্লিষ্ট app-এ নিজে action নিতে হবে।
3. **ওয়েব সার্চ:** Google বা YouTube-এ সার্চ করে browser-এ ফলাফল খোলে। এটি ওয়েবপেজ থেকে নিজে তথ্য পড়ে/যাচাই করে না এবং YouTube-এ গান চালায় না।
4. **স্থানীয় PDF/Word প্রশ্নোত্তর:** অনুমোদিত Windows drive-এ `.pdf` ও `.docx` খুঁজে text extract করে প্রাসঙ্গিক অংশ নেয়। Ollama local model পাওয়া গেলে সেখানেই উত্তর তৈরি হয়; না হলে পাওয়া উদ্ধৃতি ও file/page/paragraph citation দেখায়। Cloud AI-তে document content পাঠানো হয় না। Scanned PDF-এ OCR না থাকলে text পাওয়া নাও যেতে পারে।
5. **পণ্যের live দাম:** Star Tech, UCC, Global Brand ও Ryans-এর search listing থেকে নামের সঙ্গে মেলা BDT price, retailer link ও যাচাইয়ের সময় নেয়। কোনো source block/ব্যর্থ হলে তা জানায়; দুই বা তার বেশি source না পেলে multi-store comparison সম্পূর্ণ হয়েছে বলে দাবি করে না। দাম ও stock পরিবর্তনশীল—checkout-এর আগে retailer page যাচাই করুন।

Desktop UI-র quick actions ও toolkit-এও কেবল এই পাঁচটি সুবিধা দেখানো হয়। পুরোনো feature modules repository-তে রয়ে গেছে, কিন্তু বর্তমান VoiceMate command/UI route সেগুলো চালায় না।

---

## 📂 প্রোজেক্ট স্ট্রাকচার (Project Structure)

```
voicemate-main/
│
├── main.py                          # প্রধান এন্ট্রি পয়েন্ট (GUI ও CLI মোড)
├── run_agent.bat                    # ডাবল ক্লিকে রান করার উইন্ডোজ ব্যাচ ফাইল
├── requirements.txt                 # পাইথন ডিপেনডেন্সি তালিকা
├── config.py                        # কনফিগারেশন ফাইল
├── README.md                        # ডকুমেন্টেশন
│
├── data/
│   ├── contacts.json                # কন্টাক্ট তালিকা (নাম, ফোন)
│   ├── app_preferences.json         # অ্যাপ অনুমতি ও সেটিংস
│   └── n8n_workflows/               # 🔄 এনএইটেন এক্সপোর্টকৃত স্টার্টার ওয়ার্কফ্লো JSON
│       └── voicemate_starter_workflow.json
│
├── documents/                       # 📄 পড়া ও প্রক্রিয়াকরণের জন্য ডকুমেন্টস ফোল্ডার
│   └── test_sample.md
│
├── src/
│   ├── command_processor.py         # ভয়েস ও টেক্সট কমান্ড প্রসেসর
│   ├── agent_service.py             # ব্যাকগ্রাউন্ড লিসেনিং ও লাইফসাইকেল
│   │
│   ├── document_agent/              # 📄 PyMuPDF ডকুমেন্ট ইন্টেলিজেন্স সাবসিস্টেম
│   │   ├── __init__.py
│   │   ├── document_config.py       # ডক ফরম্যাট ও সেটিংস কনফিগারেশন
│   │   ├── pymupdf_reader.py        # PyMuPDF কোর ইঞ্জিন (Patterns A, B, C, D)
│   │   ├── document_task_runner.py  # ব্যাকগ্রাউন্ড থ্রেড রানার ও ভয়েস সামারি
│   │   └── document_fallback.py     # অল্টারনেট ফলব্যাক ডক রিডার
│   │
│   ├── docling_agent/               # 📑 IBM Docling মাল্টিমোডাল ডকুমেন্ট পার্সার ও RAG চাংকিং
│   │   ├── __init__.py
│   │   ├── docling_config.py        # ডকলিং কনফিগারেশন ও এনভায়রনমেন্ট
│   │   ├── docling_converter.py     # ইউনিভার্সাল কনভার্টার (Patterns A, B)
│   │   ├── docling_chunker.py       # হাইব্রিড সেমান্টিক চাংকার (Pattern C)
│   │   ├── docling_task_runner.py   # ব্যাকগ্রাউন্ড থ্রেড রানার ও সামারি
│   │   └── docling_fallback.py      # ফলব্যাক মাল্টিমোডাল পার্সার
│   │
│   ├── browser_agent/               # 🌐 Browser-Use 1.0 অটোনোমাস ব্রাউজার এজেন্ট
│   │   ├── __init__.py
│   │   ├── browser_config.py        # ব্রাউজার পাথ ও সেটিংস কনফিগারেশন
│   │   ├── browser_use_integration.py # ব্রাউজার-ইউজ কোর এজেন্ট ইন্টারফেস
│   │   ├── browser_task_runner.py   # ব্যাকগ্রাউন্ড থ্রেডে নন-ব্লকিং এক্সিকিউটর
│   │   └── browser_fallback.py      # ফলব্যাক ব্রাউজিং ইঞ্জিন
│   │
│   ├── playwright_agent/            # ⚡ Playwright ডিটারমিনিস্টিক ওয়েব ড্রাইভার ও অটোমেশন
│   │   ├── __init__.py
│   │   ├── playwright_config.py     # ব্রাউজার ও পাথ কনফিগারেশন
│   │   ├── playwright_controller.py # কোর অটোমেশন (Patterns A, B, C, D)
│   │   ├── playwright_task_runner.py# ব্যাকগ্রাউন্ড থ্রেড ডিসপ্যাচার
│   │   └── playwright_fallback.py   # ফলব্যাক ব্রাউজিং ও নোটিফিকেশন
│   │
│   ├── canvas_agent/                # 💻 OpenHands ডেভেলপার ক্যানভাস ও কোড ইন্টেলিজেন্স
│   │   ├── __init__.py
│   │   ├── canvas_config.py         # নোড ও পাথ কনফিগারেশন
│   │   ├── canvas_event_stream.py   # local progress/completion/error events
│   │   ├── canvas_workspace_runner.py # read-only tree, git status, Python syntax audit
│   │   ├── canvas_task_runner.py    # ব্যাকগ্রাউন্ড থ্রেড ডিসপ্যাচার
│   │   └── canvas_fallback.py       # ফলব্যাক ডেভেলপার হ্যান্ডলার
│   │
│   ├── coder_agent/                 # 🤖 Aider এআই পেয়ার প্রোগ্রামার ও কোড এডিটিং
│   │   ├── __init__.py
│   │   ├── coder_config.py          # কোডার ও ব্যাকআপ পাথ কনফিগারেশন
│   │   ├── search_replace_engine.py # SEARCH/REPLACE ব্লক প্যাচিং ইঞ্জিন (Patterns A, C)
│   │   ├── repo_map_generator.py    # AST রেপো ম্যাপ ও সিম্বল ইনডেক্সিং
│   │   ├── git_manager.py           # backup ও file-specific restore
│   │   ├── coder_task_runner.py     # ব্যাকগ্রাউন্ড থ্রেড ডিসপ্যাচার
│   │   └── coder_fallback.py        # ফলব্যাক কোড রিডার
│   │
│   ├── website_agent/               # 🏗️ Static website scaffold ও localhost preview
│   │   ├── __init__.py
│   │   └── website_controller.py    # project generation and local HTTP verification
│   │
│   ├── n8n_agent/                   # 🔄 n8n এন্টারপ্রাইজ ওয়ার্কফ্লো অটোমেশন ও ওয়েবহুক সাবসিস্টেম
│   │   ├── __init__.py
│   │   ├── n8n_config.py            # পোর্ট (5678), ওয়েবহুক পাথ ও কানেকশন চেকার
│   │   ├── n8n_workflow_template.py # ক্যানোনিকাল স্টার্টার ওয়ার্কফ্লো JSON জেনারেটর
│   │   ├── n8n_webhook_client.py    # সিঙ্ক্রোনাস ওয়েবহুক ক্লায়েন্ট (POST)
│   │   ├── n8n_fallback.py          # অফলাইন ইন্টেন্ট এমুলেশন ও ব্রাউজার ক্যানভাস লঞ্চার
│   │   ├── n8n_controller.py        # সমন্বিত ওয়ার্কফ্লো কন্ট্রোলার
│   │   └── n8n_task_runner.py       # ব্যাকগ্রাউন্ড ডেমন থ্রেড ডিসপ্যাচার
│   │
│   ├── api_gateway/                 # 🚀 FastAPI সেন্ট্রাল এপিআই গেটওয়ে ও রিয়েল-টাইম ওয়েবসকেট
│   │   ├── __init__.py
│   │   ├── api_config.py            # পোর্ট (8080), হোস্ট ও নেটওয়ার্ক কনফিগারেশন
│   │   ├── schemas.py               # Pydantic v2 টাইপড রিকোয়েস্ট/রেসপন্স মডেল
│   │   ├── app.py                   # কোর FastAPI অ্যাপ্লিকেশন, CORS ও লাইফসাইকেল
│   │   ├── server_controller.py     # ব্যাকগ্রাউন্ড Uvicorn ASGI থ্রেড কন্ট্রোলার
│   │   ├── api_task_runner.py       # ব্যাকগ্রাউন্ড ডেমন টাস্ক ডিসপ্যাচার
│   │   ├── api_fallback.py          # অফলাইন ও জিরো-ক্র্যাশ লোকাল কমান্ড হ্যান্ডলার
│   │   └── routes/                  # মডুলার APIRouter এন্ডপয়েন্টস
│   │       ├── __init__.py
│   │       ├── voice_router.py      # /api/command ও /api/speak
│   │       ├── system_router.py     # /api/system-status ও /api/health
│   │       ├── automation_router.py # /api/automation/dispatch ও n8n-webhook
│   │       └── websocket_router.py  # /ws/voice-stream ও /ws/events
│   │
│   ├── agent_brain/                 # 🧠 LangGraph সেন্ট্রাল ব্রেন ও মাল্টি-এজেন্ট স্টেট মেশিন
│   │   ├── __init__.py
│   │   ├── brain_config.py          # চেকপয়েন্ট, সেশন ও সাইক্লিক লিমিট কনফিগারেশন
│   │   ├── state_schema.py          # AgentState TypedDict ও রিডিউসার ডেফিনেশন
│   │   ├── graph_builder.py         # StateGraph তৈরি, রাউটিং ও কম্পাইলেশন
│   │   ├── brain_controller.py      # মাল্টি-টার্ন সেশন ও চেকপয়েন্ট কন্ট্রোলার
│   │   ├── brain_task_runner.py     # ব্যাকগ্রাউন্ড ডেমন টাস্ক ডিসপ্যাচার
│   │   ├── brain_fallback.py        # অফলাইন জিরো-ক্র্যাশ অর্কেস্ট্রেশন ফলব্যাক
│   │   └── workers/                 # বিশেষায়িত ওয়ার্কার নোডস
│   │       ├── __init__.py
│   │       ├── supervisor.py        # সুপারভাইজার নোড ও ইনটেন্ট রাউটার
│   │       ├── browser_worker.py    # ব্রাউজার ও ওয়েব অটোমেশন ওয়ার্কার
│   │       ├── document_worker.py   # ডকলিং ও পিডিএফ ইন্টেলিজেন্স ওয়ার্কার
│   │       ├── coding_worker.py     # এইডার ও ডেভেলপার ক্যানভাস ওয়ার্কার
│   │       ├── automation_worker.py # এনএইটেন ওয়ার্কফ্লো ওয়ার্কার
│   │       ├── system_worker.py     # ডেস্কটপ ও এপিআই গেটওয়ে ওয়ার্কার
│   │       └── conversation_worker.py # চ্যাট ও কনফার্মেশন ওয়ার্কার
│   │
│   ├── helpers/
│   │   ├── app_helper.py            # উইন্ডোজ অ্যাপ স্ক্যানার ও লঞ্চার
│   │   ├── app_preference_helper.py # অ্যাপ পারমিশন হেল্পার
│   │   ├── battery_helper.py        # ল্যাপটপ ব্যাটারি মনিটর
│   │   ├── camera_helper.py         # ওয়েবক্যাম ও স্ক্রিন ক্যাপচার
│   │   ├── contact_helper.py        # কন্টাক্ট ও ডায়াল হেল্পার
│   │   ├── date_helper.py           # বাংলা তারিখ ও সময়
│   │   ├── desktop_automation_helper.py # টাইপিং, স্ক্রলিং ও কীবোর্ড অ্যাক্সেসিবিলিটি
│   │   ├── permission_helper.py     # হার্ডওয়্যার পারমিশন হেল্পার
│   │   ├── search_helper.py         # গুগল ও ইউটিউব ব্রাউজার সার্চ
│   │   ├── sms_helper.py            # মেসেজিং হেল্পার
│   │   ├── tts_helper.py            # টেক্সট-টু-স্পিচ
│   │   ├── vision_helper.py         # OCR ও ইমেজ এনালাইসিস
│   │   └── voice_recognizer_helper.py # স্পিচ রিকগনিশন
│   │
│   └── ui/
│       ├── web_window.py            # pywebview ডেস্কটপ উইন্ডো ও Python bridge
│       └── web/                     # HTML, CSS ও JavaScript UI
│
└── tests/
    ├── test_agent.py                # সম্পূর্ণ টেস্ট স্যুট (Unit Tests)
    └── test_processor.py            # কমান্ড টেস্ট স্ক্রিপ্ট
```

---

## 🛠️ ব্যবহারের নিয়ম (How to Run)

### ধাপ ১: ডিপেনডেন্সি ইন্সটল
```bash
pip install -r requirements.txt
```

### ধাপ ২: অ্যাসিস্ট্যান্ট চালু করুন
- **ডাবল ক্লিক করে:** `run_agent.bat` ফাইলে ডাবল ক্লিক করুন।
- **টার্মিনাল থেকে GUI:** `python main.py`
- **টার্মিনাল / কনসোল মোডে:** `python main.py --cli`

---

## 🧪 টেস্ট চালান (Run Tests)
```bash
python -m unittest tests/test_agent.py
```
এবং:
```bash
python tests/test_processor.py
```
