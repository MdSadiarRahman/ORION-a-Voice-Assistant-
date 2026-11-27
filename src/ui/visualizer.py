"""
ORION AI - Orbital Energy Core Visualizer.
Real-Time Audio-Reactive 60 FPS Visualizer Engine for Tkinter.

Features:
- Central pulsing glowing orbital energy core.
- Dual counter-rotating dashed/orbital rings with particle nodes.
- Dynamic bilateral equalizer frequency spectrum bars.
- Dynamic color transitions per agent state (Idle, Listening, Thinking, Speaking).
- Extremely lightweight canvas operations optimized for low CPU usage.
"""

import math
import tkinter as tk
from typing import Optional
from src.ui.theme import AethermindTheme


class OrbitalVisualizer:
    """Audio-reactive Orbital Energy Core rendered onto a Tkinter Canvas."""

    def __init__(self, canvas: tk.Canvas, width: int = 480, height: int = 140):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.state = "idle"  # 'idle', 'listening', 'thinking', 'speaking'

        # Animation state counters
        self.pulse_phase = 0.0
        self.orbit_angle_1 = 0.0
        self.orbit_angle_2 = 0.0
        self.spectrum_data = [6.0] * 12

    def set_state(self, new_state: str) -> None:
        """Update visualizer state: 'idle', 'listening', 'thinking', 'speaking'."""
        self.state = new_state

    def update_frame(self) -> None:
        """Renders one animation frame onto the canvas."""
        c = self.canvas
        c.delete("all")

        cx = self.width // 2
        cy = self.height // 2

        # Adjust speeds based on current state
        if self.state == "listening":
            self.pulse_phase += 0.12
            self.orbit_angle_1 += 0.07
            self.orbit_angle_2 -= 0.05
            core_color = AethermindTheme.ACCENT_CYAN
            core_glow = "#083344"
            orbit_color = AethermindTheme.ACCENT_CYAN_GLOW
            spec_color = AethermindTheme.ACCENT_CYAN
            state_symbol = "🎙️"
        elif self.state == "speaking":
            self.pulse_phase += 0.10
            self.orbit_angle_1 += 0.05
            self.orbit_angle_2 -= 0.04
            core_color = AethermindTheme.ACCENT_GREEN
            core_glow = "#064E3B"
            orbit_color = AethermindTheme.ACCENT_GREEN
            spec_color = AethermindTheme.ACCENT_GREEN
            state_symbol = "🔊"
        elif self.state == "thinking":
            self.pulse_phase += 0.14
            self.orbit_angle_1 += 0.09
            self.orbit_angle_2 += 0.06
            core_color = AethermindTheme.ACCENT_AMBER
            core_glow = "#451A03"
            orbit_color = AethermindTheme.ACCENT_AMBER
            spec_color = AethermindTheme.PRIMARY_LIGHT
            state_symbol = "🧠"
        else:  # Idle
            self.pulse_phase += 0.05
            self.orbit_angle_1 += 0.02
            self.orbit_angle_2 -= 0.015
            core_color = AethermindTheme.PRIMARY
            core_glow = "#1E1B4B"
            orbit_color = AethermindTheme.PRIMARY_LIGHT
            spec_color = AethermindTheme.BORDER_GLOW_VIOLET
            state_symbol = "⚡"

        # -------------------------------------------------------------
        # 1. OUTER ENERGY AURA GLOW
        # -------------------------------------------------------------
        pulse_val = math.sin(self.pulse_phase)
        outer_r = 44 + int(5 * pulse_val)
        c.create_oval(
            cx - outer_r - 16, cy - outer_r - 16,
            cx + outer_r + 16, cy + outer_r + 16,
            fill=core_glow, outline=""
        )

        # -------------------------------------------------------------
        # 2. DUAL ROTATING ORBITAL RINGS & SATELLITE NODES
        # -------------------------------------------------------------
        # Orbit 1: Inner ring (radius 48)
        r1 = 48
        # Dashed orbital ring effect using arc segments
        for seg in range(6):
            start_ang = math.degrees(self.orbit_angle_1) + seg * 60
            c.create_arc(
                cx - r1, cy - r1, cx + r1, cy + r1,
                start=start_ang, extent=35,
                style="arc", outline=orbit_color, width=1
            )

        # Orbit 1 satellite nodes
        for node_idx in [0, 180]:
            rad = self.orbit_angle_1 + math.radians(node_idx)
            nx = cx + r1 * math.cos(rad)
            ny = cy + r1 * math.sin(rad)
            c.create_oval(nx - 3, ny - 3, nx + 3, ny + 3, fill=orbit_color, outline="")

        # Orbit 2: Outer elliptical ring (radius 66 x 58)
        r2_x, r2_y = 66, 56
        for seg in range(4):
            start_ang = math.degrees(self.orbit_angle_2) + seg * 90
            c.create_arc(
                cx - r2_x, cy - r2_y, cx + r2_x, cy + r2_y,
                start=start_ang, extent=45,
                style="arc", outline=AethermindTheme.BORDER_SUBTLE, width=1
            )

        # Orbit 2 satellite nodes
        rad2 = self.orbit_angle_2
        nx2 = cx + r2_x * math.cos(rad2)
        ny2 = cy + r2_y * math.sin(rad2)
        c.create_oval(nx2 - 2, ny2 - 2, nx2 + 2, ny2 + 2, fill=AethermindTheme.ACCENT_CYAN, outline="")

        # -------------------------------------------------------------
        # 3. CENTRAL PULSING CORE SPHERE
        # -------------------------------------------------------------
        core_r = 24 + int(3 * pulse_val)
        c.create_oval(
            cx - core_r, cy - core_r,
            cx + core_r, cy + core_r,
            fill=AethermindTheme.BG_CARD, outline=core_color, width=2
        )

        # Core symbol
        c.create_text(
            cx, cy, text=state_symbol,
            font=("Segoe UI", 13), fill=AethermindTheme.TEXT_MAIN
        )

        # -------------------------------------------------------------
        # 4. BILATERAL EQUALIZER SPECTRUM BARS
        # -------------------------------------------------------------
        num_bars = 10
        bar_width = 3
        bar_spacing = 8
        bar_offset = 80

        for i in range(num_bars):
            if self.state in ["listening", "speaking"]:
                factor = abs(math.sin(self.pulse_phase * 2.2 + i * 0.45)) * 26 + 6
            elif self.state == "thinking":
                factor = abs(math.sin(self.pulse_phase * 3.5 + i * 0.8)) * 16 + 5
            else:
                factor = abs(math.sin(self.pulse_phase * 1.0 + i * 0.35)) * 8 + 3

            bh = max(3, int(factor))

            # Left spectrum bar
            lx = cx - bar_offset - (i * bar_spacing)
            c.create_rectangle(
                lx, cy - bh, lx + bar_width, cy + bh,
                fill=spec_color, outline=""
            )

            # Right spectrum bar
            rx = cx + bar_offset + (i * bar_spacing)
            c.create_rectangle(
                rx, cy - bh, rx + bar_width, cy + bh,
                fill=spec_color, outline=""
            )
