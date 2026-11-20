"""
VoiceMate Laptop Agent - Professional Modern Desktop UI Module.
Features:
- Sleek Obsidian & Cyberpunk Indigo Dark Design System (Glassmorphic & Flat UI)
- Multi-Tab Segmented Interface (Voice & AI Chat, AI Agent Toolkit, Activity Logs)
- 60 FPS Dynamic Audio Reactive Visualizer (Orb, Equalizer Spectrum & Particle Rings)
- One-Click Quick Action Chips (Product Research, Assignment Solver, Web Builder, Media)
- Categorized AI Agent Drawer (Browser-Use, Docling, Playwright, OpenHands, Aider, n8n, LangGraph)
- Real-time System Telemetry (Engine Badge, Live Battery, Mic State)
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import threading
import math
import time
from datetime import datetime
from typing import Optional, Dict, Any

from src.agent_service import AgentService
from src.command_processor import CommandProcessor
from src.helpers.battery_helper import BatteryHelper
from src.ui.settings_window import SettingsWindow


class ModernTheme:
    """Design System tokens inspired by Catppuccin Mocha & Tokyo Night."""
    BG_DARK = "#0D0E15"           # Deep Obsidian Canvas
    BG_SURFACE = "#151722"        # Panel & Header Background
    BG_CARD = "#1B1D2C"           # Elevated Card Background
    BG_INPUT = "#222538"          # Input & Text Background
    BORDER = "#2B2E46"            # Subtle card border

    # Accents & Status Colors
    PRIMARY = "#7C3AED"           # Electric Violet
    PRIMARY_HOVER = "#6D28D9"
    ACCENT_CYAN = "#06B6D4"       # Cyber Cyan
    ACCENT_GREEN = "#10B981"      # Emerald Green (Listening / Online)
    ACCENT_AMBER = "#F59E0B"      # Amber Gold (Speaking / Busy)
    ACCENT_ROSE = "#F43F5E"       # Coral Rose (Stop / Critical)
    ACCENT_BLUE = "#3B82F6"       # Cobalt Blue

    # Text Colors
    TEXT_MAIN = "#F1F5F9"         # Primary White
    TEXT_MUTED = "#94A3B8"        # Secondary Gray
    TEXT_DIM = "#64748B"          # Hints & Timestamps


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("VoiceMate AI — Autonomous Personal Voice Agent")
        self.root.geometry("860x720")
        self.root.minsize(740, 600)
        self.root.configure(bg=ModernTheme.BG_DARK)

        # Initialize background service
        self.agent = AgentService(on_state_change=self.on_agent_state_change)

        # Animation & Visualizer State
        self.animation_angle = 0.0
        self.visualizer_state = "idle"   # 'idle', 'listening', 'speaking', 'thinking'
        self.spectrum_heights = [10.0] * 20
        self.is_running = True

        self._setup_styles()
        self._setup_ui()
        self._start_battery_updater()
        self._start_visualizer_loop()

        # Start agent service
        self.agent.start()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Tab Notebook Style
        style.configure(
            "TNotebook",
            background=ModernTheme.BG_DARK,
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            background=ModernTheme.BG_SURFACE,
            foreground=ModernTheme.TEXT_MUTED,
            padding=[16, 8],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", ModernTheme.PRIMARY), ("active", ModernTheme.BG_CARD)],
            foreground=[("selected", ModernTheme.TEXT_MAIN), ("active", ModernTheme.TEXT_MAIN)]
        )

        # Scrollbar Style
        style.configure(
            "Vertical.TScrollbar",
            background=ModernTheme.BG_CARD,
            troughcolor=ModernTheme.BG_DARK,
            borderwidth=0,
            arrowsize=10
        )

    def _setup_ui(self):
        # =========================================================
        # 1. TOP HEADER (Telemetry, Status & Engine Badge)
        # =========================================================
        header = tk.Frame(self.root, bg=ModernTheme.BG_SURFACE, height=56)
        header.pack(fill="x", side="top")

        # Brand Logo + Title
        logo_frame = tk.Frame(header, bg=ModernTheme.BG_SURFACE)
        logo_frame.pack(side="left", padx=18, pady=10)

        lbl_logo = tk.Label(
            logo_frame, text="⚡", font=("Segoe UI", 14),
            fg=ModernTheme.ACCENT_CYAN, bg=ModernTheme.BG_SURFACE
        )
        lbl_logo.pack(side="left")

        title_lbl = tk.Label(
            logo_frame, text="VoiceMate AI",
            font=("Segoe UI", 13, "bold"), fg=ModernTheme.TEXT_MAIN, bg=ModernTheme.BG_SURFACE
        )
        title_lbl.pack(side="left", padx=(6, 8))

        # Active Engine Badge (Detects Gemini API or Ollama)
        engine_name = "Gemini Cloud AI"
        try:
            import os
            if os.getenv("GEMINI_API_KEY"):
                engine_name = "Gemini 3.8 Flash ⚡"
            elif self.agent.decision_engine.ollama.is_available():
                engine_name = "Ollama Local 🦙"
            else:
                engine_name = "Autonomous NLU 🧠"
        except Exception:
            engine_name = "VoiceMate Engine"

        self.engine_badge = tk.Label(
            logo_frame, text=f" {engine_name} ",
            font=("Segoe UI", 8, "bold"),
            fg=ModernTheme.ACCENT_GREEN, bg=ModernTheme.BG_CARD,
            relief="flat", padx=6, pady=2
        )
        self.engine_badge.pack(side="left", padx=4)

        # Right Controls: Battery + Settings + Power Toggle
        header_right = tk.Frame(header, bg=ModernTheme.BG_SURFACE)
        header_right.pack(side="right", padx=16, pady=10)

        self.battery_lbl = tk.Label(
            header_right, text="🔋 --%", font=("Segoe UI", 9, "bold"),
            fg=ModernTheme.TEXT_MUTED, bg=ModernTheme.BG_SURFACE
        )
        self.battery_lbl.pack(side="left", padx=8)

        btn_settings = tk.Button(
            header_right, text="⚙️ সেটিংস",
            font=("Segoe UI", 9), fg=ModernTheme.TEXT_MAIN, bg=ModernTheme.BG_CARD,
            activebackground=ModernTheme.BORDER, activeforeground=ModernTheme.TEXT_MAIN,
            relief="flat", padx=10, pady=3, cursor="hand2", command=self._open_settings
        )
        btn_settings.pack(side="left", padx=6)

        self.btn_service_toggle = tk.Button(
            header_right, text="● লাইভ",
            font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg=ModernTheme.ACCENT_GREEN,
            activebackground=ModernTheme.PRIMARY, activeforeground="#FFFFFF",
            relief="flat", padx=10, pady=3, cursor="hand2", command=self._toggle_service
        )
        self.btn_service_toggle.pack(side="left", padx=4)

        # =========================================================
        # 2. MAIN TABBED CONTAINER
        # =========================================================
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(8, 10))

        # Tab 1: Voice & Assistant Hub (Core Interaction)
        self.tab_hub = tk.Frame(self.notebook, bg=ModernTheme.BG_DARK)
        self.notebook.add(self.tab_hub, text="🎙️ ভয়েস ও চ্যাট হাব")
        self._build_hub_tab()

        # Tab 2: AI Agent Toolkit (Organized Features)
        self.tab_toolkit = tk.Frame(self.notebook, bg=ModernTheme.BG_DARK)
        self.notebook.add(self.tab_toolkit, text="🤖 এআই এজেন্ট টুলকিট")
        self._build_toolkit_tab()

        # Tab 3: System Logs & Diagnostics
        self.tab_logs = tk.Frame(self.notebook, bg=ModernTheme.BG_DARK)
        self.notebook.add(self.tab_logs, text="📋 কার্যকলাপ ও লগ")
        self._build_logs_tab()

    # ------------------------------------------------------------------
    # TAB 1: VOICE & ASSISTANT HUB
    # ------------------------------------------------------------------
    def _build_hub_tab(self):
        # 1. Visualizer Hero Section
        vis_frame = tk.Frame(self.tab_hub, bg=ModernTheme.BG_DARK)
        vis_frame.pack(fill="x", pady=(6, 2))

        # Reactive Canvas Visualizer (Pulsing Glow & Audio Waves)
        self.canvas = tk.Canvas(
            vis_frame, width=440, height=130,
            bg=ModernTheme.BG_DARK, highlightthickness=0
        )
        self.canvas.pack(pady=4)

        # Agent State Status Banner
        self.lbl_status = tk.Label(
            vis_frame, text="অ্যাসিস্ট্যান্ট প্রস্তুত — যেকোনো ভাষায় কথা বলুন বা টাইপ করুন...",
            font=("Segoe UI", 11, "bold"), fg=ModernTheme.ACCENT_CYAN, bg=ModernTheme.BG_DARK
        )
        self.lbl_status.pack(pady=2)

        # 2. Quick Action Chips (One-Click Autonomous Workflows)
        chips_frame = tk.Frame(self.tab_hub, bg=ModernTheme.BG_DARK)
        chips_frame.pack(fill="x", padx=16, pady=4)

        chips = [
            ("📄 অ্যাসাইনমেন্ট সলভ", "Assignment 01.pdf solve kore docx e save koro"),
            ("🛍️ ল্যাপটপের দাম তুলনা", "HP laptop er dam koto compare koro"),
            ("🌐 ওয়েবসাইট বানাও", "হাসপাতাল ম্যানেজমেন্ট ওয়েবসাইট বানিয়ে সার্ভার রান করো"),
            ("🎵 গান প্লে করো", "ইউটিউবে একটি গান প্লে করো"),
            ("⚡ ব্যাটারি স্ট্যাটাস", "আমার ল্যাপটপের চার্জ কতটুকু আছে"),
        ]

        for label_text, cmd_prompt in chips:
            chip_btn = tk.Button(
                chips_frame, text=label_text,
                font=("Segoe UI", 8, "bold"),
                fg=ModernTheme.TEXT_MUTED, bg=ModernTheme.BG_CARD,
                activebackground=ModernTheme.PRIMARY, activeforeground="#FFFFFF",
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=lambda p=cmd_prompt: self._execute_chip(p)
            )
            chip_btn.pack(side="left", padx=3)

        # 3. Interactive Conversation / Chat Stream Frame
        chat_card = tk.Frame(self.tab_hub, bg=ModernTheme.BG_CARD, relief="flat", bd=1)
        chat_card.pack(fill="both", expand=True, padx=16, pady=6)

        self.chat_display = tk.Text(
            chat_card, bg=ModernTheme.BG_INPUT, fg=ModernTheme.TEXT_MAIN,
            insertbackground="white", font=("Segoe UI", 10),
            relief="flat", wrap="word", padx=12, pady=10, state="normal"
        )
        self.chat_display.pack(side="left", fill="both", expand=True)

        chat_scroll = ttk.Scrollbar(chat_card, orient="vertical", command=self.chat_display.yview)
        chat_scroll.pack(side="right", fill="y")
        self.chat_display.config(yscrollcommand=chat_scroll.set)

        # Configure Chat Tags
        self.chat_display.tag_configure("user", foreground=ModernTheme.ACCENT_CYAN, font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_configure("agent", foreground=ModernTheme.TEXT_MAIN, font=("Segoe UI", 10))
        self.chat_display.tag_configure("system", foreground=ModernTheme.TEXT_MUTED, font=("Segoe UI", 9, "italic"))
        self.chat_display.tag_configure("time", foreground=ModernTheme.TEXT_DIM, font=("Segoe UI", 8))

        # Initial Welcome Message
        self._append_chat(
            "VoiceMate",
            "স্বাগতম! আমি আপনার ইন্টেলিজেন্ট ভয়েস অ্যাসিস্ট্যান্ট।\n"
            "আপনি স্বাভাবিক বাংলা, ইংরেজি বা বাংলিশে কথা বলে কাজ করিয়ে নিতে পারেন।",
            sender_type="agent"
        )

        # 4. Modern Input Bar (Entry + Send + Voice Toggle)
        input_container = tk.Frame(self.tab_hub, bg=ModernTheme.BG_SURFACE, height=48)
        input_container.pack(fill="x", side="bottom", padx=16, pady=(4, 8))

        self.entry_cmd = tk.Entry(
            input_container, bg=ModernTheme.BG_INPUT, fg=ModernTheme.TEXT_MAIN,
            insertbackground="white", font=("Segoe UI", 10), relief="flat"
        )
        self.entry_cmd.pack(side="left", fill="x", expand=True, ipady=6, padx=(8, 8), pady=6)
        self.entry_cmd.bind("<Return>", lambda e: self._send_typed_command())

        btn_send = tk.Button(
            input_container, text="পাঠান ➤",
            font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg=ModernTheme.PRIMARY,
            activebackground=ModernTheme.PRIMARY_HOVER, activeforeground="#FFFFFF",
            relief="flat", padx=14, pady=5, cursor="hand2",
            command=self._send_typed_command
        )
        btn_send.pack(side="right", padx=(0, 6), pady=6)

    # ------------------------------------------------------------------
    # TAB 2: AI AGENT TOOLKIT
    # ------------------------------------------------------------------
    def _build_toolkit_tab(self):
        container = tk.Frame(self.tab_toolkit, bg=ModernTheme.BG_DARK)
        container.pack(fill="both", expand=True, padx=16, pady=12)

        categories = [
            {
                "title": "🌐 ইন্টারনেট ও ব্রাউজার অটোমেশন",
                "color": ModernTheme.ACCENT_CYAN,
                "tools": [
                    ("ব্রাউজার এজেন্ট", "Browser-Use দিয়ে স্বয়ংক্রিয় ব্রাউজিং", self._trigger_browser_agent),
                    ("ওয়েব অটোমেশন", "Playwright দিয়ে ক্লিক ও ডেটা স্ক্র্যাপ", self._trigger_web_automation),
                    ("প্রোডাক্ট রিসার্চ", "দারাজ ও স্টারটেকে দামের তুলনা", self._trigger_product_research),
                ]
            },
            {
                "title": "📄 ডকুমেন্ট ও অ্যাসাইনমেন্ট ইন্টেলিজেন্স",
                "color": ModernTheme.ACCENT_GREEN,
                "tools": [
                    ("ডকুমেন্ট সলভার", "PDF থেকে প্রশ্ন পড়ে DOCX সমাধান তৈরি", self._trigger_assignment_solver),
                    ("ডকলিং রিডার", "Docling দিয়ে মাল্টিমোডাল PDF/Word কনভার্ট", self._trigger_docling_converter),
                    ("PyMuPDF রিডার", "সরাসরি যেকোনো ডকুমেন্ট টেক্সট পড়া", self._trigger_doc_reader),
                ]
            },
            {
                "title": "💻 সফটওয়্যার ডেভেলপমেন্ট ও অটোমেশন",
                "color": ModernTheme.PRIMARY,
                "tools": [
                    ("ওয়েবসাইট বিল্ডার", "সম্পূর্ণ ওয়েবসাইট তৈরি ও লাইভ সার্ভার রান", self._trigger_website_builder),
                    ("এআই কোডার", "Aider দিয়ে প্রজেক্ট কোড রোলব্যাক ও অডিট", self._trigger_ai_coder),
                    ("ডেভেলপার ক্যানভাস", "OpenHands দিয়ে টার্মিনাল ও গিট কন্ট্রোল", self._trigger_developer_canvas),
                ]
            },
            {
                "title": "⚡ এন্টারপ্রাইজ ব্যাকএন্ড ও ব্রেন",
                "color": ModernTheme.ACCENT_AMBER,
                "tools": [
                    ("এনএইটেন ওয়ার্কফ্লো", "n8n অটোমেশন ও ওয়েবহুক ইন্টিগ্রেশন", self._trigger_n8n_workflow),
                    ("এপিআই গেটওয়ে", "FastAPI সোয়েগার ডক্স ও ব্যাকএন্ড সার্ভিস", self._trigger_api_gateway),
                    ("ল্যাংগ্রাফ ব্রেন", "LangGraph মাল্টি-এজেন্ট মেমোরি ও প্ল্যানিং", self._trigger_langgraph_brain),
                ]
            }
        ]

        for cat in categories:
            cat_frame = tk.LabelFrame(
                container, text=f" {cat['title']} ",
                fg=cat["color"], bg=ModernTheme.BG_SURFACE,
                font=("Segoe UI", 10, "bold"), bd=1, relief="solid"
            )
            cat_frame.pack(fill="x", pady=6)

            card_row = tk.Frame(cat_frame, bg=ModernTheme.BG_SURFACE)
            card_row.pack(fill="x", padx=8, pady=6)

            for tool_title, tool_desc, tool_action in cat["tools"]:
                t_card = tk.Frame(card_row, bg=ModernTheme.BG_CARD, padx=8, pady=6, relief="flat")
                t_card.pack(side="left", fill="both", expand=True, padx=4)

                tk.Label(
                    t_card, text=tool_title,
                    font=("Segoe UI", 9, "bold"), fg=ModernTheme.TEXT_MAIN, bg=ModernTheme.BG_CARD
                ).pack(anchor="w")

                tk.Label(
                    t_card, text=tool_desc,
                    font=("Segoe UI", 8), fg=ModernTheme.TEXT_MUTED, bg=ModernTheme.BG_CARD,
                    wraplength=190, justify="left"
                ).pack(anchor="w", pady=(2, 6))

                btn_launch = tk.Button(
                    t_card, text="লঞ্চ করুন ➜",
                    font=("Segoe UI", 8, "bold"), fg=ModernTheme.TEXT_MAIN, bg=ModernTheme.PRIMARY,
                    activebackground=ModernTheme.PRIMARY_HOVER, activeforeground="#FFFFFF",
                    relief="flat", padx=8, pady=2, cursor="hand2", command=tool_action
                )
                btn_launch.pack(anchor="w")

    # ------------------------------------------------------------------
    # TAB 3: LOGS & DIAGNOSTICS
    # ------------------------------------------------------------------
    def _build_logs_tab(self):
        log_frame = tk.Frame(self.tab_logs, bg=ModernTheme.BG_DARK)
        log_frame.pack(fill="both", expand=True, padx=16, pady=10)

        # Log Header
        top_bar = tk.Frame(log_frame, bg=ModernTheme.BG_DARK)
        top_bar.pack(fill="x", pady=(0, 6))

        tk.Label(
            top_bar, text="রিয়েল-টাইম সিস্টেম টেলিমেট্রি ও ইভেন্ট লগ:",
            font=("Segoe UI", 10, "bold"), fg=ModernTheme.TEXT_MUTED, bg=ModernTheme.BG_DARK
        ).pack(side="left")

        btn_clear = tk.Button(
            top_bar, text="লগ মুছুন",
            font=("Segoe UI", 8), fg=ModernTheme.TEXT_MAIN, bg=ModernTheme.BG_CARD,
            relief="flat", padx=8, pady=2, cursor="hand2", command=self._clear_logs
        )
        btn_clear.pack(side="right")

        self.txt_log = tk.Text(
            log_frame, bg=ModernTheme.BG_INPUT, fg=ModernTheme.TEXT_MAIN,
            insertbackground="white", font=("Consolas", 9),
            relief="flat", wrap="word"
        )
        self.txt_log.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.txt_log.yview)
        scrollbar.pack(side="right", fill="y")
        self.txt_log.config(yscrollcommand=scrollbar.set)

    # ------------------------------------------------------------------
    # DYNAMIC AUDIO REACTIVE VISUALIZER (60 FPS Engine)
    # ------------------------------------------------------------------
    def _draw_visualizer(self):
        self.canvas.delete("all")
        w, h = 440, 130
        cx, cy = w // 2, h // 2

        self.animation_angle += 0.08

        # 1. Background Aura Glow
        state = self.visualizer_state
        if state == "listening":
            glow_color = "#042F2C"
            ring_color = ModernTheme.ACCENT_GREEN
            core_icon = "🎙️"
        elif state == "speaking":
            glow_color = "#2E1065"
            ring_color = ModernTheme.PRIMARY
            core_icon = "🔊"
        elif state == "thinking":
            glow_color = "#351C05"
            ring_color = ModernTheme.ACCENT_AMBER
            core_icon = "🧠"
        else:
            glow_color = "#161927"
            ring_color = ModernTheme.ACCENT_CYAN
            core_icon = "✨"

        # Outer Soft Pulsing Ring
        pulse_r = 38 + int(6 * math.sin(self.animation_angle))
        self.canvas.create_oval(
            cx - pulse_r - 12, cy - pulse_r - 12,
            cx + pulse_r + 12, cy + pulse_r + 12,
            fill=glow_color, outline=""
        )

        # Mid Ring
        self.canvas.create_oval(
            cx - pulse_r, cy - pulse_r,
            cx + pulse_r, cy + pulse_r,
            fill=ModernTheme.BG_CARD, outline=ring_color, width=2
        )

        # 2. Dynamic Audio Equalizer Spectrum Bars (Left & Right)
        num_bars = 10
        bar_w = 4
        spacing = 7

        for i in range(num_bars):
            # Calculate dynamic height based on sin waves and energy
            if state in ["listening", "speaking"]:
                h_factor = math.sin(self.animation_angle * 2.5 + i * 0.4) * 22 + 10
            elif state == "thinking":
                h_factor = math.sin(self.animation_angle * 4.0 + i * 0.8) * 12 + 8
            else:
                h_factor = math.sin(self.animation_angle + i * 0.3) * 6 + 4

            bar_h = max(4, int(abs(h_factor)))

            # Left side bars
            lx = cx - 55 - (i * spacing)
            self.canvas.create_rectangle(
                lx, cy - bar_h, lx + bar_w, cy + bar_h,
                fill=ring_color, outline=""
            )

            # Right side bars
            rx = cx + 55 + (i * spacing)
            self.canvas.create_rectangle(
                rx, cy - bar_h, rx + bar_w, cy + bar_h,
                fill=ring_color, outline=""
            )

        # Core Emoji Icon
        self.canvas.create_text(
            cx, cy, text=core_icon, font=("Segoe UI", 16)
        )

    def _start_visualizer_loop(self):
        try:
            if not self.root.winfo_exists():
                return
            self._draw_visualizer()
            self.root.after(35, self._start_visualizer_loop)  # ~30-40 FPS smooth UI tick
        except Exception:
            pass

    # ------------------------------------------------------------------
    # STATE MANAGEMENT & INTERACTION
    # ------------------------------------------------------------------
    def on_agent_state_change(self, state: dict):
        def _update():
            try:
                if not self.root.winfo_exists():
                    return
                msg = state.get("message", "")
                is_listening = state.get("is_listening", False)
                is_speaking = state.get("is_speaking", False)
                is_typing = state.get("is_typing_mode", False)

                if is_speaking:
                    self.visualizer_state = "speaking"
                    self.lbl_status.config(text="অ্যাসিস্ট্যান্ট কথা বলছে...", fg=ModernTheme.PRIMARY)
                elif is_typing:
                    self.visualizer_state = "listening"
                    self.lbl_status.config(text="টাইপিং মোড সক্রিয় — যা লিখতে চান বলুন...", fg=ModernTheme.ACCENT_CYAN)
                elif is_listening:
                    self.visualizer_state = "listening"
                    self.lbl_status.config(text="শুনছি... আপনার অনুরোধটি বলুন", fg=ModernTheme.ACCENT_GREEN)
                else:
                    self.visualizer_state = "idle"
                    self.lbl_status.config(text="অ্যাসিস্ট্যান্ট প্রস্তুত — বলুন আমি কীভাবে সাহায্য করতে পারি...", fg=ModernTheme.TEXT_MUTED)

                if msg:
                    self.log(msg)
                    if any(w in msg for w in ["শোনা গেছে:", "ইউটিউবে", "সমাধান", "দাম", "চার্জ"]):
                        if msg.startswith("শোনা গেছে:"):
                            self._append_chat("আপনি", msg.replace("শোনা গেছে:", "").strip(), sender_type="user")
                        else:
                            self._append_chat("VoiceMate", msg, sender_type="agent")
            except Exception:
                pass

        try:
            if self.root.winfo_exists():
                self.root.after(0, _update)
        except Exception:
            pass

    def _append_chat(self, sender: str, text: str, sender_type: str = "agent"):
        try:
            timestamp = datetime.now().strftime("%I:%M %p")
            self.chat_display.config(state="normal")
            
            if sender_type == "user":
                self.chat_display.insert(tk.END, f"\n👤 {sender}  ", "user")
                self.chat_display.insert(tk.END, f"[{timestamp}]\n", "time")
                self.chat_display.insert(tk.END, f"{text}\n", "agent")
            else:
                self.chat_display.insert(tk.END, f"\n🤖 {sender}  ", "agent")
                self.chat_display.insert(tk.END, f"[{timestamp}]\n", "time")
                self.chat_display.insert(tk.END, f"{text}\n", "agent")
            
            self.chat_display.see(tk.END)
        except Exception:
            pass

    def log(self, text: str):
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.txt_log.insert(tk.END, f"[{timestamp}] {text}\n")
            self.txt_log.see(tk.END)
        except Exception:
            pass

    def _clear_logs(self):
        self.txt_log.delete("1.0", tk.END)

    def _send_typed_command(self):
        query = self.entry_cmd.get().strip()
        if not query:
            return
        self.entry_cmd.delete(0, tk.END)
        self._append_chat("আপনি", query, sender_type="user")
        self.log(f"> {query}")
        self.visualizer_state = "thinking"
        self.lbl_status.config(text="প্রসেস করা হচ্ছে...", fg=ModernTheme.ACCENT_AMBER)
        threading.Thread(target=self.agent.process_results, args=(query,), daemon=True).start()

    def _execute_chip(self, prompt: str):
        self.entry_cmd.delete(0, tk.END)
        self.entry_cmd.insert(0, prompt)
        self._send_typed_command()

    # ------------------------------------------------------------------
    # AGENT TOOLKIT ACTIONS
    # ------------------------------------------------------------------
    def _trigger_product_research(self):
        item = simpledialog.askstring(
            "প্রোডাক্ট ও প্রাইস রিসার্চ",
            "কোন প্রোডাক্টের দাম ও স্পেক যাচাই করতে চান?\n(যেমন: 'HP laptop 50000 taka' বা 'Samsung Galaxy A55')",
            parent=self.root
        )
        if item and item.strip():
            self._execute_chip(f"খুঁজে দাও {item.strip()} দাম কত")

    def _trigger_assignment_solver(self):
        file_path = filedialog.askopenfilename(
            title="সমাধানের জন্য অ্যাসাইনমেন্ট PDF নির্বাচন করুন",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")],
            parent=self.root
        )
        if file_path:
            from pathlib import Path
            filename = Path(file_path).name
            self._execute_chip(f"{filename} solve kore docx e save koro")

    def _trigger_website_builder(self):
        idea = simpledialog.askstring(
            "ওয়েবসাইট বিল্ডার এজেন্ট",
            "কী ধরনের ওয়েবসাইট তৈরি করতে চান?\n(যেমন: 'Hospital Management System' বা 'E-Commerce store')",
            parent=self.root
        )
        if idea and idea.strip():
            self._execute_chip(f"{idea.strip()} ওয়েবসাইট বানিয়ে সার্ভার চালু করো")

    def _trigger_browser_agent(self):
        task = simpledialog.askstring(
            "ব্রাউজার এজেন্ট (Browser-Use 1.0)",
            "ব্রাউজারে গিয়ে এজেন্ট কি কাজ করবে লিখুন:\n(যেমন: 'গিটহাবে গিয়ে ভয়েসমেট সার্চ করো')",
            parent=self.root
        )
        if task and task.strip():
            self._execute_chip(f"ব্রাউজারে গিয়ে {task.strip()}")

    def _trigger_doc_reader(self):
        file_path = filedialog.askopenfilename(
            title="পড়ার জন্য ডকুমেন্ট নির্বাচন করুন",
            filetypes=[("All Supported Files", "*.pdf *.xps *.epub *.txt *.md"), ("All Files", "*.*")],
            parent=self.root
        )
        if file_path:
            self._execute_chip(f"ডকুমেন্ট পড়ো {file_path}")

    def _trigger_docling_converter(self):
        file_path = filedialog.askopenfilename(
            title="ডকলিং দিয়ে কনভার্ট ও চাংক করার জন্য ফাইল নির্বাচন করুন",
            filetypes=[("Documents", "*.pdf *.docx *.pptx *.xlsx *.html *.csv *.txt *.md"), ("All Files", "*.*")],
            parent=self.root
        )
        if file_path:
            self._execute_chip(f"ডকলিং ডকুমেন্ট কনভার্ট {file_path}")

    def _trigger_web_automation(self):
        cmd = simpledialog.askstring(
            "ওয়েব অটোমেশন (Playwright)",
            "কমান্ড লিখুন:\n- 'স্ক্রিনশট নাও https://github.com'\n- 'হোয়াটসঅ্যাপ ওয়েব ওপেন করো'",
            parent=self.root
        )
        if cmd and cmd.strip():
            self._execute_chip(cmd.strip())

    def _trigger_developer_canvas(self):
        cmd = simpledialog.askstring(
            "ওপেনহ্যান্ডস ক্যানভাস (OpenHands)",
            "কমান্ড লিখুন: 'ক্যানভাস চালু করো' / 'কোড অডিট করো' / 'টার্মিনালে চালাও dir'",
            parent=self.root
        )
        if cmd and cmd.strip():
            self._execute_chip(cmd.strip())

    def _trigger_ai_coder(self):
        cmd = simpledialog.askstring(
            "এইডার এআই কোডার (Aider)",
            "কমান্ড লিখুন: 'রেপো ম্যাপ তৈরি করো' / 'কোড রোলব্যাক করো'",
            parent=self.root
        )
        if cmd and cmd.strip():
            self._execute_chip(cmd.strip())

    def _trigger_n8n_workflow(self):
        cmd = simpledialog.askstring(
            "এনএইটেন ওয়ার্কফ্লো (n8n)",
            "কমান্ড লিখুন: 'এনএইটেন খোলো' / 'ইমেইল পাঠাও'",
            parent=self.root
        )
        if cmd and cmd.strip():
            self._execute_chip(cmd.strip())

    def _trigger_api_gateway(self):
        cmd = simpledialog.askstring(
            "ফাস্টএপিআই গেটওয়ে (FastAPI)",
            "কমান্ড লিখুন: 'এপিআই ওপেন করো' / 'এপিআই স্ট্যাটাস'",
            parent=self.root
        )
        if cmd and cmd.strip():
            self._execute_chip(cmd.strip())

    def _trigger_langgraph_brain(self):
        cmd = simpledialog.askstring(
            "ল্যাংগ্রাফ ব্রেন (LangGraph)",
            "কমান্ড লিখুন: 'ব্রেন স্ট্যাটাস' / 'ব্রেন হিস্ট্রি'",
            parent=self.root
        )
        if cmd and cmd.strip():
            self._execute_chip(cmd.strip())

    def _toggle_service(self):
        if self.agent.is_running:
            self.agent.stop()
            self.btn_service_toggle.config(text="● বন্ধ", bg=ModernTheme.ACCENT_ROSE)
            self.lbl_status.config(text="সার্ভিস সাময়িকভাবে বন্ধ আছে", fg=ModernTheme.ACCENT_ROSE)
            self.log("[সার্ভিস সাময়িকভাবে বন্ধ করা হয়েছে]")
        else:
            self.agent.start()
            self.btn_service_toggle.config(text="● লাইভ", bg=ModernTheme.ACCENT_GREEN)
            self.lbl_status.config(text="সার্ভিস পুনরায় চালু হয়েছে", fg=ModernTheme.ACCENT_GREEN)
            self.log("[সার্ভিস চালু করা হয়েছে]")

    def _start_battery_updater(self):
        def update():
            try:
                if not self.root.winfo_exists():
                    return
                info = BatteryHelper.get_battery_info()
                pct = info.get("percent", -1)
                charging = info.get("charging", False)
                if pct >= 0:
                    icon = "⚡" if charging else "🔋"
                    self.battery_lbl.config(text=f"{icon} {pct}%")
                self.root.after(30000, update)
            except Exception:
                pass
        update()

    def _open_settings(self):
        SettingsWindow(self.root)

    def _exit_app(self):
        try:
            self.is_running = False
            self.agent.stop()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
