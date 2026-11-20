"""
VoiceMate Laptop Agent - FastAPI Server Controller.
Manages the lifecycle of the uvicorn ASGI server in background daemon threads,
preventing VoiceMate GUI and voice recognition from freezing.
"""
import logging
import threading
import time
import webbrowser
from typing import Optional, Dict, Any
import uvicorn
from .api_config import (
    API_HOST,
    API_PORT,
    API_DOCS_URL,
    API_BASE_URL,
    is_port_in_use,
)
from .app import app

logger = logging.getLogger("VoiceMate.APIGateway.Controller")

class APIServerController:
    """Controls the lifecycle of the FastAPI / Uvicorn server."""
    _server_instance: Optional[uvicorn.Server] = None
    _server_thread: Optional[threading.Thread] = None
    _is_running: bool = False
    _host: str = API_HOST
    _port: int = API_PORT

    @classmethod
    def start_server(cls, host: str = API_HOST, port: int = API_PORT, open_docs: bool = True) -> Dict[str, Any]:
        """
        Starts the FastAPI ASGI server inside a daemon thread using Uvicorn.
        """
        cls._host = host
        cls._port = port

        # Check if already running
        if cls.is_running():
            docs_url = f"http://{cls._host}:{cls._port}/docs"
            if open_docs:
                cls.open_docs_in_browser()
            return {
                "status": "already_running",
                "host": cls._host,
                "port": cls._port,
                "url": f"http://{cls._host}:{cls._port}",
                "docs_url": docs_url,
                "message": f"এপিআই গেটওয়ে ইতিমধ্যে সক্রিয় রয়েছে: {docs_url}"
            }

        try:
            # Configure uvicorn programmatic server
            config = uvicorn.Config(
                app=app,
                host=cls._host,
                port=cls._port,
                log_level="warning",
                access_log=False,
                loop="asyncio"
            )
            cls._server_instance = uvicorn.Server(config)

            def _run():
                cls._is_running = True
                logger.info(f"FastAPI ASGI Server running at http://{cls._host}:{cls._port}")
                try:
                    cls._server_instance.run()
                except Exception as e:
                    logger.error(f"Uvicorn server crashed: {e}")
                finally:
                    cls._is_running = False

            cls._server_thread = threading.Thread(
                target=_run,
                name="VoiceMate-FastAPI-Server",
                daemon=True
            )
            cls._server_thread.start()

            # Wait briefly for startup
            for _ in range(20):
                time.sleep(0.1)
                if is_port_in_use(cls._port, cls._host):
                    break

            docs_url = f"http://{cls._host}:{cls._port}/docs"
            if open_docs:
                cls.open_docs_in_browser()

            return {
                "status": "started",
                "host": cls._host,
                "port": cls._port,
                "url": f"http://{cls._host}:{cls._port}",
                "docs_url": docs_url,
                "message": f"এপিআই গেটওয়ে সার্ভার চালু হয়েছে: {docs_url}"
            }

        except Exception as e:
            logger.error(f"Failed to start FastAPI server: {e}")
            cls._is_running = False
            return {
                "status": "error",
                "error": str(e),
                "message": f"এপিআই সার্ভার চালু করতে ত্রুটি: {e}"
            }

    @classmethod
    def stop_server(cls) -> Dict[str, Any]:
        """Gracefully stops the active FastAPI server."""
        if cls._server_instance and cls._is_running:
            try:
                cls._server_instance.should_exit = True
                cls._is_running = False
                logger.info("FastAPI server stop requested.")
                return {
                    "status": "stopped",
                    "message": "এপিআই সার্ভার বন্ধ করা হয়েছে।"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "message": f"সার্ভার বন্ধ করতে ত্রুটি: {e}"
                }
        return {
            "status": "not_running",
            "message": "এপিআই সার্ভার বর্তমানে বন্ধ রয়েছে।"
        }

    @classmethod
    def is_running(cls) -> bool:
        """Returns True if the server thread is alive and port is responding."""
        if cls._is_running and cls._server_thread and cls._server_thread.is_alive():
            return True
        return is_port_in_use(cls._port, cls._host)

    @classmethod
    def open_docs_in_browser(cls) -> bool:
        """Opens interactive Swagger UI documentation in user's default browser."""
        url = f"http://{cls._host}:{cls._port}/docs"
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            logger.warning(f"Could not open browser for API docs: {e}")
            return False

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns status dictionary of the FastAPI gateway."""
        running = cls.is_running()
        return {
            "running": running,
            "host": cls._host,
            "port": cls._port,
            "base_url": f"http://{cls._host}:{cls._port}",
            "docs_url": f"http://{cls._host}:{cls._port}/docs",
            "redoc_url": f"http://{cls._host}:{cls._port}/redoc"
        }
