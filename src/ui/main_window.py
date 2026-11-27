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
from src.ui.theme import AethermindTheme, ModernTheme
from src.ui.visualizer import OrbitalVisualizer


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ORION — a Voice Assistant")
        self.root.geometry("860x720")
        self.root.minsize(740, 600)
        self.root.configure(bg=ModernTheme.BG_DARK)

        # Initialize background service
        self.agent = AgentService(on_state_change=self.on_agent_state_change)

        # Animation & Visualizer State
        self.animation_angle = 0.0
        self.visualizer_state = "idle"   # 'idle', 'listening', 'speaking', 'thinking'
        self.visualizer: Optional[OrbitalVisualizer] = None
        self.spectrum_heights = [10.0] * 20
        self.is_running = True

        self._setup_styles()
        self._setup_ui()
        self._show_launch_splash()
        self._start_battery_updater()
        self._start_visualizer_loop()

        # Start agent service
        self.agent.start()

    def _setup_styles(self):
        style = ttk.Style()
        AethermindTheme.apply_ttk_styles(style)

    def _setup_ui(self):
        # =========================================================
        # 1. TOP TELEMETRY HUD HEADER (Frosted Glass & Sci-Fi Accent)
        # =========================================================
        header = tk.Frame(self.root, bg=AethermindTheme.BG_SURFACE, height=52)
        header.pack(fill="x", side="top")

        # Subtle bottom neon accent line
        hud_accent = tk.Frame(self.root, bg=AethermindTheme.BORDER_SUBTLE, height=1)
        hud_accent.pack(fill="x", side="top")

        # --- Left: Glowing Title Emblem & Animated Status Dot ---
        logo_frame = tk.Frame(header, bg=AethermindTheme.BG_SURFACE)
        logo_frame.pack(side="left", padx=16, pady=8)

        lbl_logo = tk.Label(
            logo_frame, text="⚡", font=("Segoe UI", 13),
            fg=AethermindTheme.ACCENT_CYAN, bg=AethermindTheme.BG_SURFACE
        )
        lbl_logo.pack(side="left")

        title_lbl = tk.Label(
            logo_frame, text="ORION AI",
            font=("Segoe UI", 11, "bold"), fg=AethermindTheme.TEXT_MAIN, bg=AethermindTheme.BG_SURFACE
        )
        title_lbl.pack(side="left", padx=(6, 8))

        # Live Status Telemetry Pill (Dot + ONLINE / LISTENING / OFFLINE)
        status_frame = tk.Frame(
            logo_frame,
            bg=AethermindTheme.BG_CARD,
            highlightthickness=1,
            highlightbackground=AethermindTheme.BORDER_SUBTLE,
            padx=7, pady=2
        )
        status_frame.pack(side="left", padx=(4, 6))

        self.status_dot = tk.Label(
            status_frame, text="●", font=("Segoe UI", 8),
            fg=AethermindTheme.ACCENT_GREEN, bg=AethermindTheme.BG_CARD
        )
        self.status_dot.pack(side="left", padx=(0, 4))

        self.status_badge = tk.Label(
            status_frame, text="ONLINE", font=("Consolas", 8, "bold"),
            fg=AethermindTheme.ACCENT_GREEN, bg=AethermindTheme.BG_CARD
        )
        self.status_badge.pack(side="left")

        # --- Right: Engine Pill + Battery + Settings + Service Toggle ---
        header_right = tk.Frame(header, bg=AethermindTheme.BG_SURFACE)
        header_right.pack(side="right", padx=14, pady=8)

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
            engine_name = "ORION Engine"

        engine_pill = tk.Frame(
            header_right,
            bg=AethermindTheme.BG_CARD,
            highlightthickness=1,
            highlightbackground=AethermindTheme.BORDER_SUBTLE,
            padx=8, pady=3
        )
        engine_pill.pack(side="left", padx=4)

        self.engine_badge = tk.Label(
            engine_pill, text=f"⚡ {engine_name}",
            font=("Segoe UI", 8, "bold"),
            fg=AethermindTheme.ACCENT_CYAN, bg=AethermindTheme.BG_CARD
        )
        self.engine_badge.pack(side="left")

        # Battery Telemetry Pill
        battery_pill = tk.Frame(
            header_right,
            bg=AethermindTheme.BG_CARD,
            highlightthickness=1,
            highlightbackground=AethermindTheme.BORDER_SUBTLE,
            padx=8, pady=3
        )
        battery_pill.pack(side="left", padx=4)

        self.battery_lbl = tk.Label(
            battery_pill, text="🔋 --%", font=("Segoe UI", 9, "bold"),
            fg=AethermindTheme.TEXT_MUTED, bg=AethermindTheme.BG_CARD
        )
        self.battery_lbl.pack(side="left")

        # Settings Icon Button
        btn_settings = tk.Button(
            header_right, text="⚙️ সেটিংস",
            font=("Segoe UI", 9), fg=AethermindTheme.TEXT_MAIN, bg=AethermindTheme.BG_CARD,
            activebackground=AethermindTheme.BG_CARD_HOVER, activeforeground=AethermindTheme.TEXT_MAIN,
            highlightthickness=1, highlightbackground=AethermindTheme.BORDER_SUBTLE,
            relief="flat", padx=10, pady=3, cursor="hand2", command=self._open_settings
        )
        btn_settings.pack(side="left", padx=4)

        # Subtle UI Audio / SFX Mute-Unmute Toggle
        self.sound_enabled = False
        self.btn_audio_toggle = tk.Button(
            header_right, text="🔇",
            font=("Segoe UI", 9), fg=AethermindTheme.TEXT_MUTED, bg=AethermindTheme.BG_CARD,
            activebackground=AethermindTheme.BG_CARD_HOVER, activeforeground=AethermindTheme.TEXT_MAIN,
            highlightthickness=1, highlightbackground=AethermindTheme.BORDER_SUBTLE,
            relief="flat", padx=8, pady=3, cursor="hand2", command=self._toggle_ui_audio
        )
        self.btn_audio_toggle.pack(side="left", padx=4)

        # Live Service Neon Pill Switch
        self.btn_service_toggle = tk.Button(
            header_right, text="● লাইভ",
            font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg=AethermindTheme.ACCENT_GREEN,
            activebackground=AethermindTheme.PRIMARY, activeforeground="#FFFFFF",
            highlightthickness=1, highlightbackground=AethermindTheme.BORDER_SUBTLE,
            relief="flat", padx=12, pady=3, cursor="hand2", command=self._toggle_service
        )
        self.btn_service_toggle.pack(side="left", padx=(4, 6))

        # =========================================================
        # 2. FLOATING SEGMENTED PILL NAVIGATION BAR
        # =========================================================
        nav_container = tk.Frame(self.root, bg=AethermindTheme.BG_SPACE)
        nav_container.pack(fill="x", padx=16, pady=(8, 2))

        nav_pill_bar = tk.Frame(
            nav_container,
            bg=AethermindTheme.BG_CARD,
            highlightthickness=1,
            highlightbackground=AethermindTheme.BORDER_SUBTLE,
            padx=3,
            pady=3
        )
        nav_pill_bar.pack(anchor="center")

        self.nav_buttons = []
        tabs_data = [
            ("🎙️ ভয়েস ও চ্যাট হাব", 0),
            ("🤖 এআই এজেন্ট টুলকিট", 1),
            ("📋 কার্যকলাপ ও লগ", 2),
        ]
        for label_text, tab_idx in tabs_data:
            btn = tk.Button(
                nav_pill_bar,
                text=label_text,
                font=("Segoe UI", 9, "bold"),
                padx=16,
                pady=5,
                relief="flat",
                cursor="hand2",
                command=lambda idx=tab_idx: self._switch_tab(idx)
            )
            btn.pack(side="left", padx=2)
            self._bind_nav_hover(btn, tab_idx)
            self.nav_buttons.append(btn)

        # =========================================================
        # 3. MAIN TABBED CONTAINER (Tabs driven by Segmented Bar)
        # =========================================================
        self.notebook = ttk.Notebook(self.root, style="Hidden.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(4, 10))

        # Tab 1: Voice & Assistant Hub (Core Interaction)
        self.tab_hub = tk.Frame(self.notebook, bg=AethermindTheme.BG_DARK)
        self.notebook.add(self.tab_hub, text="🎙️ ভয়েস ও চ্যাট হাব")
        self._build_hub_tab()

        # Tab 2: AI Agent Toolkit (Organized Features)
        self.tab_toolkit = tk.Frame(self.notebook, bg=AethermindTheme.BG_DARK)
        self.notebook.add(self.tab_toolkit, text="🤖 এআই এজেন্ট টুলকিট")
        self._build_toolkit_tab()

        # Tab 3: System Logs & Diagnostics
        self.tab_logs = tk.Frame(self.notebook, bg=AethermindTheme.BG_DARK)
        self.notebook.add(self.tab_logs, text="📋 কার্যকলাপ ও লগ")
        self._build_logs_tab()

        # Set default active tab
        self.current_tab_idx = 0
        self._switch_tab(0)

    def _bind_nav_hover(self, btn: tk.Button, tab_idx: int):
        def on_enter(e):
            if self.current_tab_idx != tab_idx:
                btn.config(bg=AethermindTheme.BG_CARD_HOVER, fg=AethermindTheme.TEXT_MAIN)
        def on_leave(e):
            if self.current_tab_idx != tab_idx:
                btn.config(bg=AethermindTheme.BG_CARD, fg=AethermindTheme.TEXT_MUTED)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def _show_launch_splash(self):
        """Immersive Sci-Fi launch splash overlay that smoothly dismisses."""
        self.splash_overlay = tk.Frame(self.root, bg=AethermindTheme.BG_SPACE)
        self.splash_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        center_frame = tk.Frame(self.splash_overlay, bg=AethermindTheme.BG_SPACE)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Concentric glowing orbital rings
        canvas = tk.Canvas(center_frame, width=120, height=120, bg=AethermindTheme.BG_SPACE, highlightthickness=0)
        canvas.pack(pady=8)
        canvas.create_oval(15, 15, 105, 105, outline=AethermindTheme.BORDER_GLOW_VIOLET, width=2)
        canvas.create_oval(30, 30, 90, 90, outline=AethermindTheme.ACCENT_CYAN, width=1)
        canvas.create_oval(45, 45, 75, 75, fill=AethermindTheme.PRIMARY, outline="")
        canvas.create_text(60, 60, text="⚡", font=("Segoe UI", 16), fill="#FFFFFF")

        lbl_title = tk.Label(
            center_frame, text="ORION AI",
            font=("Segoe UI", 16, "bold"), fg=AethermindTheme.TEXT_MAIN, bg=AethermindTheme.BG_SPACE
        )
        lbl_title.pack(pady=(4, 2))

        lbl_sub = tk.Label(
            center_frame, text="INITIALIZING NEURAL CORE...",
            font=("Consolas", 10, "bold"), fg=AethermindTheme.ACCENT_CYAN, bg=AethermindTheme.BG_SPACE
        )
        lbl_sub.pack(pady=4)

        lbl_hint = tk.Label(
            center_frame, text="[ Click anywhere to enter command center ]",
            font=("Segoe UI", 8), fg=AethermindTheme.TEXT_DIM, bg=AethermindTheme.BG_SPACE
        )
        lbl_hint.pack(pady=8)

        def dismiss(e=None):
            if getattr(self, "splash_overlay", None) and self.splash_overlay.winfo_exists():
                self.splash_overlay.destroy()
                self.splash_overlay = None

        self.splash_overlay.bind("<Button-1>", dismiss)
        canvas.bind("<Button-1>", dismiss)
        lbl_title.bind("<Button-1>", dismiss)
        lbl_sub.bind("<Button-1>", dismiss)
        lbl_hint.bind("<Button-1>", dismiss)
        self.root.after(1500, dismiss)

    def _toggle_ui_audio(self):
        self.sound_enabled = not getattr(self, "sound_enabled", False)
        if self.sound_enabled:
            self.btn_audio_toggle.config(text="🔊", fg=AethermindTheme.ACCENT_CYAN)
            self._play_ui_sfx("click")
        else:
            self.btn_audio_toggle.config(text="🔇", fg=AethermindTheme.TEXT_MUTED)

    def _play_ui_sfx(self, sfx_type: str = "click"):
        if not getattr(self, "sound_enabled", False):
            return
        try:
            import winsound
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception:
            pass

    def _switch_tab(self, index: int):
        self.current_tab_idx = index
        self.notebook.select(index)
        self._play_ui_sfx("click")
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.config(
                    bg=AethermindTheme.PRIMARY,
                    fg=AethermindTheme.TEXT_MAIN,
                    activebackground=AethermindTheme.PRIMARY_HOVER,
                    activeforeground=AethermindTheme.TEXT_MAIN
                )
            else:
                btn.config(
                    bg=AethermindTheme.BG_CARD,
                    fg=AethermindTheme.TEXT_MUTED,
                    activebackground=AethermindTheme.BG_CARD_HOVER,
                    activeforeground=AethermindTheme.TEXT_MAIN
                )

    # ------------------------------------------------------------------
    # TAB 1: VOICE & ASSISTANT HUB
    # ------------------------------------------------------------------
    def _bind_chip_hover(self, btn: tk.Button):
        def on_enter(e):
            btn.config(bg=AethermindTheme.BG_CARD_HOVER, fg=AethermindTheme.ACCENT_CYAN_GLOW, highlightbackground=AethermindTheme.BORDER_GLOW_CYAN)
        def on_leave(e):
            btn.config(bg=AethermindTheme.BG_CARD, fg=AethermindTheme.TEXT_MUTED, highlightbackground=AethermindTheme.BORDER_SUBTLE)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def _build_hub_tab(self):
        # 1. Orbital Visualizer Hero Section
        vis_frame = tk.Frame(self.tab_hub, bg=AethermindTheme.BG_SPACE)
        vis_frame.pack(fill="x", pady=(4, 0))

        # Solar-Orbit Reactive Canvas Visualizer
        self.canvas = tk.Canvas(
            vis_frame, width=480, height=135,
            bg=AethermindTheme.BG_SPACE, highlightthickness=0
        )
        self.canvas.pack(pady=(2, 0))
        self.visualizer = OrbitalVisualizer(self.canvas, width=480, height=135)

        # Agent State Status Banner
        self.lbl_status = tk.Label(
            vis_frame, text="অ্যাসিস্ট্যান্ট প্রস্তুত — যেকোনো ভাষায় কথা বলুন বা টাইপ করুন...",
            font=("Segoe UI", 10, "bold"), fg=AethermindTheme.ACCENT_CYAN, bg=AethermindTheme.BG_SPACE
        )
        self.lbl_status.pack(pady=2)

        # 2. One-Click Quick Action Chips (Sleek Sci-Fi Horizontal Pills)
        chips_frame = tk.Frame(self.tab_hub, bg=AethermindTheme.BG_SPACE)
        chips_frame.pack(fill="x", padx=16, pady=(2, 6))

        chips_inner = tk.Frame(chips_frame, bg=AethermindTheme.BG_SPACE)
        chips_inner.pack(anchor="center")

        chips = [
            ("📄 Solve Assignment", "Assignment 01.pdf solve kore docx e save koro"),
            ("🛍️ Compare Prices", "HP laptop er dam koto compare koro"),
            ("🌐 Build Website", "হাসপাতাল ম্যানেজমেন্ট ওয়েবসাইট বানিয়ে সার্ভার রান করো"),
            ("🎵 Play Music", "ইউটিউবে একটি গান প্লে করো"),
            ("⚡ Battery Status", "আমার ল্যাপটপের চার্জ কতটুকু আছে"),
        ]

        for label_text, cmd_prompt in chips:
            chip_btn = tk.Button(
                chips_inner, text=label_text,
                font=("Segoe UI", 8, "bold"),
                fg=AethermindTheme.TEXT_MUTED, bg=AethermindTheme.BG_CARD,
                activebackground=AethermindTheme.PRIMARY, activeforeground="#FFFFFF",
                highlightthickness=1, highlightbackground=AethermindTheme.BORDER_SUBTLE,
                relief="flat", padx=10, pady=4, cursor="hand2",
                command=lambda p=cmd_prompt: self._execute_chip(p)
            )
            chip_btn.pack(side="left", padx=4)
            self._bind_chip_hover(chip_btn)

        # 3. Modern Glassmorphic Chat Stream Frame
        chat_card = tk.Frame(
            self.tab_hub,
            bg=AethermindTheme.BG_CARD,
            highlightthickness=1,
            highlightbackground=AethermindTheme.BORDER_SUBTLE
        )
        chat_card.pack(fill="both", expand=True, padx=16, pady=(2, 6))

        self.chat_display = tk.Text(
            chat_card, bg=AethermindTheme.BG_INPUT, fg=AethermindTheme.TEXT_MAIN,
            insertbackground=AethermindTheme.ACCENT_CYAN, font=("Segoe UI", 10),
            relief="flat", wrap="word", padx=14, pady=10, state="normal"
        )
        self.chat_display.pack(side="left", fill="both", expand=True)

        chat_scroll = ttk.Scrollbar(chat_card, orient="vertical", command=self.chat_display.yview)
        chat_scroll.pack(side="right", fill="y")
        self.chat_display.config(yscrollcommand=chat_scroll.set)

        # Configure Chat Bubble Tags
        self.chat_display.tag_configure("user_hdr", justify="right", foreground=AethermindTheme.PRIMARY_LIGHT, font=("Segoe UI", 9, "bold"))
        self.chat_display.tag_configure("user_msg", justify="right", foreground=AethermindTheme.TEXT_MAIN, font=("Segoe UI", 10), rmargin=10)
        self.chat_display.tag_configure("user_time", justify="right", foreground=AethermindTheme.TEXT_DIM, font=("Consolas", 8))

        self.chat_display.tag_configure("agent_hdr", justify="left", foreground=AethermindTheme.ACCENT_CYAN, font=("Segoe UI", 9, "bold"))
        self.chat_display.tag_configure("agent_msg", justify="left", foreground=AethermindTheme.TEXT_MAIN, font=("Segoe UI", 10), lmargin1=10, lmargin2=10)
        self.chat_display.tag_configure("agent_time", justify="left", foreground=AethermindTheme.TEXT_DIM, font=("Consolas", 8))

        self.chat_display.tag_configure("system", justify="center", foreground=AethermindTheme.TEXT_MUTED, font=("Segoe UI", 9, "italic"))

        # Initial Welcome Message
        self._append_chat(
            "ORION AI",
            "স্বাগতম! আমি আপনার ইন্টেলিজেন্ট অটোনোমাস ভয়েস অ্যাসিস্ট্যান্ট।\n"
            "আপনি স্বাভাবিক বাংলা, ইংরেজি বা বাংলিশে কথা বলে কাজ করিয়ে নিতে পারেন।",
            sender_type="agent"
        )

        # 4. Floating Rounded Command Dock (Entry + Mic Icon + Send Button)
        dock_container = tk.Frame(self.tab_hub, bg=AethermindTheme.BG_SPACE)
        dock_container.pack(fill="x", side="bottom", padx=16, pady=(2, 8))

        input_dock = tk.Frame(
            dock_container,
            bg=AethermindTheme.BG_SURFACE,
            highlightthickness=1,
            highlightbackground=AethermindTheme.BORDER_SUBTLE,
            padx=8, pady=4
        )
        input_dock.pack(fill="x")

        # Left mic indicator icon
        lbl_mic = tk.Label(
            input_dock, text="🎙️",
            font=("Segoe UI", 11),
            fg=AethermindTheme.ACCENT_CYAN,
            bg=AethermindTheme.BG_SURFACE,
            cursor="hand2"
        )
        lbl_mic.pack(side="left", padx=(4, 6))

        self.entry_cmd = tk.Entry(
            input_dock, bg=AethermindTheme.BG_SURFACE, fg=AethermindTheme.TEXT_MAIN,
            insertbackground=AethermindTheme.ACCENT_CYAN, font=("Segoe UI", 10), relief="flat"
        )
        self.entry_cmd.pack(side="left", fill="x", expand=True, ipady=4, padx=4)
        self.entry_cmd.bind("<Return>", lambda e: self._send_typed_command())

        # Cyan focus glow on entry focus
        self.entry_cmd.bind("<FocusIn>", lambda e: input_dock.config(highlightbackground=AethermindTheme.BORDER_GLOW_CYAN))
        self.entry_cmd.bind("<FocusOut>", lambda e: input_dock.config(highlightbackground=AethermindTheme.BORDER_SUBTLE))

        btn_send = tk.Button(
            input_dock, text="পাঠান ➤",
            font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg=AethermindTheme.PRIMARY,
            activebackground=AethermindTheme.PRIMARY_HOVER, activeforeground="#FFFFFF",
            relief="flat", padx=14, pady=4, cursor="hand2",
            command=self._send_typed_command
        )
        btn_send.pack(side="right", padx=(4, 2))

    # ------------------------------------------------------------------
    # TAB 2: AI AGENT TOOLKIT (2x2 Sci-Fi Mission Cards)
    # ------------------------------------------------------------------
    def _build_toolkit_tab(self):
        container = tk.Frame(self.tab_toolkit, bg=AethermindTheme.BG_SPACE)
        container.pack(fill="both", expand=True, padx=14, pady=8)

        # 2x2 Responsive Grid
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        quadrants = [
            {
                "row": 0, "col": 0,
                "icon": "🌐",
                "title": "ইন্টারনেট ও ব্রাউজার অটোমেশন",
                "subtitle": "স্বয়ংক্রিয় ওয়েব ব্রাউজিং, ডেটা স্ক্র্যাপিং ও প্রাইস রিসার্চ",
                "accent": AethermindTheme.ACCENT_CYAN,
                "tools": [
                    ("ব্রাউজার এজেন্ট", "Browser-Use দিয়ে ওয়েবসাইট ভিজিট ও ফর্ম ফিলআপ", self._trigger_browser_agent),
                    ("ওয়েব অটোমেশন", "Playwright দিয়ে ক্লিক, টাইপ ও ডেটা এক্সট্রাক্ট", self._trigger_web_automation),
                    ("প্রোডাক্ট রিসার্চ", "দারাজ ও স্টারটেকে পণ্যের রিয়েল-টাইম দাম যাচাই", self._trigger_product_research),
                ]
            },
            {
                "row": 0, "col": 1,
                "icon": "📄",
                "title": "ডকুমেন্ট ও অ্যাসাইনমেন্ট ইন্টেলিজেন্স",
                "subtitle": "মাল্টিমোডাল PDF বিশ্লেষণ, ডকলিং ও DOCX সমাধান ইঞ্জিন",
                "accent": AethermindTheme.ACCENT_GREEN,
                "tools": [
                    ("ডকুমেন্ট সলভার", "PDF থেকে প্রশ্ন পড়ে DOCX ফরম্যাটে পূর্ণ সমাধান তৈরি", self._trigger_assignment_solver),
                    ("ডকলিং কনভার্টার", "Docling দিয়ে PDF/Word মাল্টিমোডাল চাংকিং ও রূপান্তর", self._trigger_docling_converter),
                    ("PyMuPDF রিডার", "সরাসরি যেকোনো ডকুমেন্ট টেক্সট দ্রুত রিড ও সামারি", self._trigger_doc_reader),
                ]
            },
            {
                "row": 1, "col": 0,
                "icon": "💻",
                "title": "সফটওয়্যার ডেভেলপমেন্ট ও অটোমেশন",
                "subtitle": "স্বয়ংক্রিয় ওয়েবসাইট নির্মাণ, গিট ও কোড অডিট সহকারী",
                "accent": AethermindTheme.PRIMARY_LIGHT,
                "tools": [
                    ("ওয়েবসাইট বিল্ডার", "সম্পূর্ণ ওয়েবসাইট তৈরি ও লাইভ লোকাল সার্ভার রান", self._trigger_website_builder),
                    ("এআই কোডার", "Aider দিয়ে প্রজেক্ট কোড রোলব্যাক ও স্ট্রাকচার অডিট", self._trigger_ai_coder),
                    ("ডেভেলপার ক্যানভাস", "OpenHands দিয়ে টার্মিনাল ও গিট কনসোল কন্ট্রোল", self._trigger_developer_canvas),
                ]
            },
            {
                "row": 1, "col": 1,
                "icon": "⚡",
                "title": "এন্টারপ্রাইজ ব্যাকএন্ড ও ব্রেন",
                "subtitle": "n8n ওয়েবহুক, সোয়েগার API ও LangGraph মাল্টি-এজেন্ট মেমোরি",
                "accent": AethermindTheme.ACCENT_AMBER,
                "tools": [
                    ("এনএইটেন ওয়ার্কফ্লো", "n8n অটোমেশন পাইপলাইন ও ওয়েবহুক ইন্টিগ্রেশন", self._trigger_n8n_workflow),
                    ("এপিআই গেটওয়ে", "FastAPI সোয়েগার ডক্স ও ব্যাকএন্ড মাইক্রোসার্ভিস", self._trigger_api_gateway),
                    ("ল্যাংগ্রাফ ব্রেন", "LangGraph মাল্টি-এজেন্ট স্টেট ও ডিসিশন প্ল্যানিং", self._trigger_langgraph_brain),
                ]
            }
        ]

        for quad in quadrants:
            # Sci-Fi Mission Card
            card = tk.Frame(
                container,
                bg=AethermindTheme.BG_CARD,
                highlightthickness=1,
                highlightbackground=AethermindTheme.BORDER_SUBTLE,
                padx=12,
                pady=8
            )
            card.grid(row=quad["row"], column=quad["col"], padx=6, pady=6, sticky="nsew")

            # Header: Glowing Icon + Title + Status Pill
            hdr = tk.Frame(card, bg=AethermindTheme.BG_CARD)
            hdr.pack(fill="x", pady=(0, 2))

            lbl_icon = tk.Label(
                hdr, text=quad["icon"], font=("Segoe UI", 12),
                fg=quad["accent"], bg=AethermindTheme.BG_CARD
            )
            lbl_icon.pack(side="left")

            lbl_title = tk.Label(
                hdr, text=f" {quad['title']}",
                font=("Segoe UI", 10, "bold"), fg=AethermindTheme.TEXT_MAIN, bg=AethermindTheme.BG_CARD
            )
            lbl_title.pack(side="left")

            badge = tk.Label(
                hdr, text="● READY",
                font=("Consolas", 8, "bold"), fg=AethermindTheme.ACCENT_GREEN, bg=AethermindTheme.BG_SURFACE,
                highlightthickness=1, highlightbackground=AethermindTheme.BORDER_SUBTLE,
                padx=6, pady=2
            )
            badge.pack(side="right")

            # Subtitle
            tk.Label(
                card, text=quad["subtitle"],
                font=("Segoe UI", 8), fg=AethermindTheme.TEXT_DIM, bg=AethermindTheme.BG_CARD,
                anchor="w"
            ).pack(fill="x", pady=(0, 6))

            # Tool Rows inside Card
            for tool_title, tool_desc, tool_action in quad["tools"]:
                t_row = tk.Frame(
                    card, bg=AethermindTheme.BG_SURFACE,
                    highlightthickness=1, highlightbackground=AethermindTheme.BORDER_SUBTLE,
                    padx=8, pady=4
                )
                t_row.pack(fill="x", pady=3)

                info_col = tk.Frame(t_row, bg=AethermindTheme.BG_SURFACE)
                info_col.pack(side="left", fill="both", expand=True)

                tk.Label(
                    info_col, text=tool_title,
                    font=("Segoe UI", 9, "bold"), fg=AethermindTheme.TEXT_MAIN, bg=AethermindTheme.BG_SURFACE
                ).pack(anchor="w")

                tk.Label(
                    info_col, text=tool_desc,
                    font=("Segoe UI", 8), fg=AethermindTheme.TEXT_MUTED, bg=AethermindTheme.BG_SURFACE
                ).pack(anchor="w")

                btn_launch = tk.Button(
                    t_row, text="লঞ্চ ➜",
                    font=("Segoe UI", 8, "bold"), fg="#FFFFFF", bg=quad["accent"],
                    activebackground=AethermindTheme.PRIMARY_HOVER, activeforeground="#FFFFFF",
                    relief="flat", padx=10, pady=2, cursor="hand2", command=tool_action
                )
                btn_launch.pack(side="right", padx=(4, 0))

            # Hover Border Glow Feedback
            self._bind_card_hover(card, quad["accent"])

    def _bind_card_hover(self, card: tk.Frame, glow_color: str):
        def on_enter(e):
            card.config(highlightbackground=glow_color)
        def on_leave(e):
            card.config(highlightbackground=AethermindTheme.BORDER_SUBTLE)
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

    # ------------------------------------------------------------------
    # TAB 3: LOGS & DIAGNOSTICS (Cyber Telemetry Console)
    # ------------------------------------------------------------------
    def _build_logs_tab(self):
        log_frame = tk.Frame(self.tab_logs, bg=AethermindTheme.BG_SPACE)
        log_frame.pack(fill="both", expand=True, padx=14, pady=8)

        # Top Control Bar
        top_bar = tk.Frame(log_frame, bg=AethermindTheme.BG_SPACE)
        top_bar.pack(fill="x", pady=(0, 6))

        tk.Label(
            top_bar, text="⚡ লাইভ সিস্টেম টেলিমেট্রি কনসোল:",
            font=("Segoe UI", 10, "bold"), fg=AethermindTheme.ACCENT_CYAN, bg=AethermindTheme.BG_SPACE
        ).pack(side="left")

        # Clear Logs Button
        btn_clear = tk.Button(
            top_bar, text="🗑️ লগ মুছুন",
            font=("Segoe UI", 8, "bold"), fg=AethermindTheme.TEXT_MAIN, bg=AethermindTheme.BG_CARD,
            activebackground=AethermindTheme.BG_CARD_HOVER, activeforeground=AethermindTheme.TEXT_MAIN,
            highlightthickness=1, highlightbackground=AethermindTheme.BORDER_SUBTLE,
            relief="flat", padx=10, pady=3, cursor="hand2", command=self._clear_logs
        )
        btn_clear.pack(side="right", padx=(4, 0))

        # Auto-Scroll Toggle
        self.auto_scroll_var = tk.BooleanVar(value=True)
        chk_scroll = tk.Checkbutton(
            top_bar, text="Auto-Scroll", variable=self.auto_scroll_var,
            font=("Segoe UI", 8, "bold"), fg=AethermindTheme.TEXT_MUTED, bg=AethermindTheme.BG_SPACE,
            selectcolor=AethermindTheme.BG_CARD, activebackground=AethermindTheme.BG_SPACE,
            activeforeground=AethermindTheme.TEXT_MAIN, cursor="hand2"
        )
        chk_scroll.pack(side="right", padx=6)

        # Quick Filter Entry
        self.entry_log_filter = tk.Entry(
            top_bar, bg=AethermindTheme.BG_INPUT, fg=AethermindTheme.TEXT_MAIN,
            insertbackground=AethermindTheme.ACCENT_CYAN, font=("Consolas", 9),
            relief="flat", width=18
        )
        self.entry_log_filter.pack(side="right", padx=6, ipady=2)
        self.entry_log_filter.insert(0, "🔍 ফিল্টার...")
        self.entry_log_filter.bind("<FocusIn>", lambda e: self.entry_log_filter.delete(0, tk.END) if self.entry_log_filter.get() == "🔍 ফিল্টার..." else None)
        self.entry_log_filter.bind("<KeyRelease>", lambda e: self._filter_logs())

        # Terminal Console Box
        console_card = tk.Frame(
            log_frame, bg=AethermindTheme.BG_CARD,
            highlightthickness=1, highlightbackground=AethermindTheme.BORDER_SUBTLE
        )
        console_card.pack(fill="both", expand=True)

        self.txt_log = tk.Text(
            console_card, bg=AethermindTheme.BG_SPACE_DEEP, fg=AethermindTheme.TEXT_MAIN,
            insertbackground=AethermindTheme.ACCENT_CYAN, font=("Consolas", 9),
            relief="flat", wrap="word", padx=12, pady=10
        )
        self.txt_log.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(console_card, orient="vertical", command=self.txt_log.yview)
        scrollbar.pack(side="right", fill="y")
        self.txt_log.config(yscrollcommand=scrollbar.set)

        # Configure Color-Coded Log Tags
        self.txt_log.tag_configure("tag_time", foreground=AethermindTheme.TEXT_DIM, font=("Consolas", 9))
        self.txt_log.tag_configure("tag_info", foreground=AethermindTheme.ACCENT_CYAN, font=("Consolas", 9, "bold"))
        self.txt_log.tag_configure("tag_agent", foreground=AethermindTheme.PRIMARY_LIGHT, font=("Consolas", 9, "bold"))
        self.txt_log.tag_configure("tag_success", foreground=AethermindTheme.ACCENT_GREEN, font=("Consolas", 9, "bold"))
        self.txt_log.tag_configure("tag_warn", foreground=AethermindTheme.ACCENT_AMBER, font=("Consolas", 9, "bold"))
        self.txt_log.tag_configure("tag_error", foreground=AethermindTheme.ACCENT_ROSE, font=("Consolas", 9, "bold"))
        self.txt_log.tag_configure("tag_msg", foreground=AethermindTheme.TEXT_MAIN, font=("Consolas", 9))

        self.raw_log_entries = []

    # ------------------------------------------------------------------
    # DYNAMIC AUDIO REACTIVE VISUALIZER (60 FPS Engine)
    # ------------------------------------------------------------------
    def _draw_visualizer(self):
        if self.visualizer:
            self.visualizer.set_state(self.visualizer_state)
            self.visualizer.update_frame()

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
                    self.status_dot.config(fg=AethermindTheme.PRIMARY_LIGHT)
                    self.status_badge.config(text="SPEAKING", fg=AethermindTheme.PRIMARY_LIGHT)
                elif is_typing:
                    self.visualizer_state = "listening"
                    self.lbl_status.config(text="টাইপিং মোড সক্রিয় — যা লিখতে চান বলুন...", fg=ModernTheme.ACCENT_CYAN)
                    self.status_dot.config(fg=AethermindTheme.ACCENT_CYAN)
                    self.status_badge.config(text="TYPING", fg=AethermindTheme.ACCENT_CYAN)
                elif is_listening:
                    self.visualizer_state = "listening"
                    self.lbl_status.config(text="শুনছি... আপনার অনুরোধটি বলুন", fg=ModernTheme.ACCENT_GREEN)
                    self.status_dot.config(fg=AethermindTheme.ACCENT_GREEN)
                    self.status_badge.config(text="LISTENING", fg=AethermindTheme.ACCENT_GREEN)
                else:
                    self.visualizer_state = "idle"
                    self.lbl_status.config(text="অ্যাসিস্ট্যান্ট প্রস্তুত — বলুন আমি কীভাবে সাহায্য করতে পারি...", fg=ModernTheme.TEXT_MUTED)
                    self.status_dot.config(fg=AethermindTheme.ACCENT_GREEN)
                    self.status_badge.config(text="ONLINE", fg=AethermindTheme.ACCENT_GREEN)

                if msg:
                    self.log(msg)
                    if any(w in msg for w in ["শোনা গেছে:", "ইউটিউবে", "সমাধান", "দাম", "চার্জ"]):
                        if msg.startswith("শোনা গেছে:"):
                            self._append_chat("আপনি", msg.replace("শোনা গেছে:", "").strip(), sender_type="user")
                        else:
                            self._append_chat("ORION", msg, sender_type="agent")
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
                self.chat_display.insert(tk.END, f"\n{sender} 👤  ", "user_hdr")
                self.chat_display.insert(tk.END, f"[{timestamp}]\n", "user_time")
                self.chat_display.insert(tk.END, f"{text}\n", "user_msg")
            else:
                self.chat_display.insert(tk.END, f"\n◈ {sender}  ", "agent_hdr")
                self.chat_display.insert(tk.END, f"[{timestamp}]\n", "agent_time")
                self.chat_display.insert(tk.END, f"│ {text}\n", "agent_msg")
            
            self.chat_display.see(tk.END)
        except Exception:
            pass

    def log(self, text: str):
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            if not hasattr(self, "raw_log_entries"):
                self.raw_log_entries = []
            self.raw_log_entries.append((timestamp, text))
            self._render_log_entry(timestamp, text)
        except Exception:
            pass

    def _render_log_entry(self, timestamp: str, text: str):
        try:
            self.txt_log.config(state="normal")
            self.txt_log.insert(tk.END, f"[{timestamp}] ", "tag_time")

            lower_text = text.lower()
            if any(k in lower_text for k in ["[error]", "ত্রুটি", "failed", "exception"]):
                tag_type = "tag_error"
                tag_badge = "[ERROR] "
            elif any(k in lower_text for k in ["[warn]", "সতর্কতা", "warning"]):
                tag_type = "tag_warn"
                tag_badge = "[WARN] "
            elif any(k in lower_text for k in ["[success]", "সফল", "complete", "pass"]):
                tag_type = "tag_success"
                tag_badge = "[SUCCESS] "
            elif any(k in lower_text for k in ["[agent]", ">", "এজেন্ট", "action", "plan"]):
                tag_type = "tag_agent"
                tag_badge = "[AGENT] "
            else:
                tag_type = "tag_info"
                tag_badge = "[INFO] "

            self.txt_log.insert(tk.END, tag_badge, tag_type)
            self.txt_log.insert(tk.END, f"{text}\n", "tag_msg")

            if getattr(self, "auto_scroll_var", None) and self.auto_scroll_var.get():
                self.txt_log.see(tk.END)
        except Exception:
            pass

    def _clear_logs(self):
        try:
            if hasattr(self, "raw_log_entries"):
                self.raw_log_entries.clear()
            self.txt_log.delete("1.0", tk.END)
        except Exception:
            pass

    def _filter_logs(self):
        try:
            query = self.entry_log_filter.get().strip().lower()
            if query == "🔍 ফিল্টার...":
                query = ""
            self.txt_log.delete("1.0", tk.END)
            for ts, txt in getattr(self, "raw_log_entries", []):
                if not query or query in txt.lower():
                    self._render_log_entry(ts, txt)
        except Exception:
            pass

    def _send_typed_command(self):
        query = self.entry_cmd.get().strip()
        if not query:
            return
        self._play_ui_sfx("click")
        self.entry_cmd.delete(0, tk.END)
        self._append_chat("আপনি", query, sender_type="user")
        self.log(f"> {query}")
        self.visualizer_state = "thinking"
        self.lbl_status.config(text="প্রসেস করা হচ্ছে...", fg=ModernTheme.ACCENT_AMBER)
        self.status_dot.config(fg=AethermindTheme.ACCENT_AMBER)
        self.status_badge.config(text="THINKING", fg=AethermindTheme.ACCENT_AMBER)
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
            self.status_dot.config(fg=AethermindTheme.ACCENT_ROSE)
            self.status_badge.config(text="OFFLINE", fg=AethermindTheme.ACCENT_ROSE)
            self.log("[সার্ভিস সাময়িকভাবে বন্ধ করা হয়েছে]")
        else:
            self.agent.start()
            self.btn_service_toggle.config(text="● লাইভ", bg=ModernTheme.ACCENT_GREEN)
            self.lbl_status.config(text="সার্ভিস পুনরায় চালু হয়েছে", fg=ModernTheme.ACCENT_GREEN)
            self.status_dot.config(fg=AethermindTheme.ACCENT_GREEN)
            self.status_badge.config(text="ONLINE", fg=AethermindTheme.ACCENT_GREEN)
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
