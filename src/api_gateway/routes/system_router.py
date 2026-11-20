"""
VoiceMate Laptop Agent - System Status API Router.
Provides real-time system metrics, battery level, power state, and module availability.
"""
import ctypes
import os
from typing import Dict, Any, List
from fastapi import APIRouter
from ..schemas import SystemStatusResponse
from ...helpers.battery_helper import BatteryHelper
import config

router = APIRouter(prefix="/api", tags=["System & Metrics"])

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

def _get_memory_load() -> float:
    """Gets memory usage percentage using native Windows API or psutil."""
    try:
        import psutil
        return float(psutil.virtual_memory().percent)
    except Exception:
        pass

    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return float(stat.dwMemoryLoad)
    except Exception:
        pass
    return 0.0

def _get_cpu_percent() -> float:
    """Gets CPU utilization percentage."""
    try:
        import psutil
        return float(psutil.cpu_percent(interval=None))
    except Exception:
        return 0.0

def _get_active_subsystems() -> List[str]:
    """Returns list of enabled agent subsystems."""
    modules = ["voice_agent", "fastapi_gateway"]
    if getattr(config, "BROWSER_USE_ENABLED", True):
        modules.append("browser_agent")
    if getattr(config, "PLAYWRIGHT_ENABLED", True):
        modules.append("playwright_agent")
    if getattr(config, "DOCLING_ENABLED", True):
        modules.append("docling_agent")
    if getattr(config, "CODER_ENABLED", True):
        modules.append("coder_agent")
    if getattr(config, "CANVAS_ENABLED", True):
        modules.append("canvas_agent")
    if getattr(config, "N8N_ENABLED", True):
        modules.append("n8n_agent")
    return modules

@router.get("/system-status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Returns real-time laptop battery percentage, AC power connection,
    CPU and memory usage, and all active agent subsystems.
    """
    battery_info = BatteryHelper.get_battery_info()
    return SystemStatusResponse(
        cpu_percent=_get_cpu_percent(),
        battery_percent=battery_info.get("percent") if battery_info else None,
        is_plugged=battery_info.get("charging") if battery_info else None,
        memory_percent=_get_memory_load(),
        active_modules=_get_active_subsystems()
    )

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Lightweight service health check endpoint."""
    return {
        "status": "healthy",
        "service": "VoiceMate Core Agent API",
        "version": config.VERSION,
        "mode": "Desktop Agent",
        "port": getattr(config, "API_PORT", 8080)
    }

@router.get("/modules")
async def list_modules() -> Dict[str, Any]:
    """Returns list of all available and active VoiceMate agent modules."""
    return {
        "active_modules": _get_active_subsystems(),
        "total_modules": len(_get_active_subsystems())
    }
