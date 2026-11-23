"""
ORION AI - Aethermind Design System & Styling Tokens.
Aethermind Deep-Space / Cyber-Orbital Command Center Theme.

Provides:
- Color palette tokens (Deep Space, Glassmorphic Card, Cosmic Violet, Neon Cyan)
- Typography definitions with full Bengali Unicode fallback (Nirmala UI / Hind Siliguri)
- TTK Style application helper
- Backward-compatible alias ModernTheme
"""

from dataclasses import dataclass
from tkinter import ttk
from typing import Tuple


class AethermindTheme:
    """Aethermind Deep Space & Cyber-Orbital Command Center Design Tokens."""

    # 1. Backgrounds & Surfaces
    BG_SPACE = "#07080F"            # Deep Space Base Canvas
    BG_SPACE_DEEP = "#0D0E1A"       # Dark Orbital Canvas
    BG_SURFACE = "#121422"          # Top HUD & Glassmorphic Surface
    BG_CARD = "#161829"             # Elevated Mission Card / Panel
    BG_CARD_HOVER = "#20233A"       # Hovered Card Surface
    BG_INPUT = "#1F2238"            # Text Field & Terminal Background
    BG_OVERLAY = "#0A0B14"          # Floating Overlay Surface

    # Backward compatibility with existing ModernTheme attributes
    BG_DARK = BG_SPACE

    # 2. Glowing Borders & Dividers
    BORDER_SUBTLE = "#282A42"       # 1px Subtle Glass Border
    BORDER_GLOW_VIOLET = "#7C3AED"  # Cosmic Violet Border Glow
    BORDER_GLOW_CYAN = "#06B6D4"    # Neon Cyan Border Glow
    BORDER = BORDER_SUBTLE          # Alias for legacy compatibility

    # 3. Core Accents & Telemetry Colors
    PRIMARY = "#7C3AED"             # Cosmic Violet
    PRIMARY_HOVER = "#9333EA"       # Electric Violet Hover
    PRIMARY_LIGHT = "#A78BFA"       # Soft Violet Highlight

    ACCENT_CYAN = "#06B6D4"         # Neon Cyan
    ACCENT_CYAN_GLOW = "#22D3EE"    # Cyan Pulse / Highlight
    ACCENT_GREEN = "#10B981"        # Emerald Pulse (Online / Listening)
    ACCENT_AMBER = "#F59E0B"        # Amber Gold (Thinking / Planning)
    ACCENT_ROSE = "#F43F5E"         # Crimson / Coral (Alert / Offline)
    ACCENT_BLUE = "#3B82F6"         # Cobalt Blue (Telemetry)

    # 4. Typography Colors
    TEXT_MAIN = "#F8FAFC"           # Crisp Primary White
    TEXT_MUTED = "#94A3B8"          # Secondary Cool Gray
    TEXT_DIM = "#64748B"            # Timestamps, Subtitles & Hints
    TEXT_CYAN = "#22D3EE"           # High-priority telemetry text
    TEXT_VIOLET = "#C4B5FD"         # Soft Violet Accent text

    # 5. Visualizer Aura Glows
    GLOW_IDLE = "#161927"
    GLOW_LISTENING = "#042F2E"
    GLOW_SPEAKING = "#2E1065"
    GLOW_THINKING = "#351C05"

    # 6. Typography with Bengali Unicode Fallback (Segoe UI + Nirmala UI)
    FONT_FAMILY = "Segoe UI"
    FONT_FALLBACK = "Nirmala UI"

    FONT_TITLE = ("Segoe UI", 13, "bold")
    FONT_SUBTITLE = ("Segoe UI", 11, "bold")
    FONT_BODY = ("Segoe UI", 10)
    FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
    FONT_BODY_ITALIC = ("Segoe UI", 9, "italic")
    FONT_SMALL = ("Segoe UI", 8)
    FONT_SMALL_BOLD = ("Segoe UI", 8, "bold")
    FONT_BADGE = ("Segoe UI", 8, "bold")
    FONT_BUTTON = ("Segoe UI", 9, "bold")
    FONT_MONO = ("Consolas", 9)
    FONT_MONO_BOLD = ("Consolas", 9, "bold")

    @classmethod
    def apply_ttk_styles(cls, style: ttk.Style) -> None:
        """Configures ttk widget styles with Aethermind Sci-Fi theme tokens."""
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Tab Notebook
        style.configure(
            "TNotebook",
            background=cls.BG_SPACE,
            borderwidth=0,
            tabmargins=[0, 0, 0, 0],
        )
        style.configure(
            "TNotebook.Tab",
            background=cls.BG_SURFACE,
            foreground=cls.TEXT_MUTED,
            padding=[18, 9],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            focuscolor=cls.PRIMARY,
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", cls.PRIMARY),
                ("active", cls.BG_CARD_HOVER),
            ],
            foreground=[
                ("selected", cls.TEXT_MAIN),
                ("active", cls.TEXT_MAIN),
            ],
        )

        # Hidden Tab Notebook (for floating Segmented Pill Navigation)
        style.layout("Hidden.TNotebook.Tab", [])
        style.configure("Hidden.TNotebook", background=cls.BG_SPACE, borderwidth=0)

        # Scrollbar
        style.configure(
            "Vertical.TScrollbar",
            background=cls.BG_CARD,
            troughcolor=cls.BG_SPACE,
            borderwidth=0,
            arrowsize=11,
            gripcount=0,
        )
        style.map(
            "Vertical.TScrollbar",
            background=[
                ("active", cls.PRIMARY),
                ("pressed", cls.PRIMARY_HOVER),
            ],
        )

        # Progressbar
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor=cls.BG_INPUT,
            background=cls.ACCENT_CYAN,
            borderwidth=0,
            thickness=6,
        )


# Backward compatibility alias
ModernTheme = AethermindTheme
