"""
VoiceMate Laptop Agent - WebSocket Real-Time Stream Router.
Implements Pattern B: Full-duplex WebSocket streaming for low-latency live audio tokens,
voice dictation chunks, and real-time agent activity broadcast.
"""
import json
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...command_processor import CommandProcessor

logger = logging.getLogger("VoiceMate.APIGateway.WebSocket")
router = APIRouter(tags=["Real-Time WebSockets"])

# Active connections for agent event broadcasting
_active_event_subscribers: Set[WebSocket] = set()

async def broadcast_agent_event(event_type: str, data: dict):
    """Broadcasts an agent event or log update to all connected WebSocket clients."""
    payload = json.dumps({"event": event_type, "data": data}, ensure_ascii=False)
    disconnected = set()
    for ws in _active_event_subscribers:
        try:
            await ws.send_text(payload)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        _active_event_subscribers.discard(ws)

@router.websocket("/ws/voice-stream")
async def voice_stream_endpoint(websocket: WebSocket):
    """
    Pattern B: Real-Time Low-Latency Voice / Audio Stream.
    Receives raw speech tokens, audio chunks, or dictation sentences from mobile or web,
    processes them through VoiceMate in real time, and responds immediately.
    """
    await websocket.accept()
    logger.info("Voice stream client connected.")
    try:
        while True:
            # Receive streamed token or JSON payload
            raw_data = await websocket.receive_text()
            token = raw_data.strip()
            if not token:
                continue

            # Process command or stream token
            try:
                data_json = json.loads(token)
                command_text = data_json.get("command", "")
            except Exception:
                command_text = token

            if command_text:
                result = CommandProcessor.process_command(command_text)
                response_payload = {
                    "input": command_text,
                    "result": result,
                    "status": "processed"
                }
            else:
                response_payload = {
                    "input": token,
                    "status": "acknowledged"
                }

            await websocket.send_text(json.dumps(response_payload, ensure_ascii=False))

    except WebSocketDisconnect:
        logger.info("Voice stream client disconnected gracefully.")
    except Exception as e:
        logger.warning(f"Voice stream error: {e}")

@router.websocket("/ws/events")
async def agent_events_endpoint(websocket: WebSocket):
    """
    Subscribes client to live agent events, status updates, and execution logs.
    """
    await websocket.accept()
    _active_event_subscribers.add(websocket)
    logger.info(f"Agent event subscriber added. Total subscribers: {len(_active_event_subscribers)}")
    try:
        await websocket.send_text(json.dumps({
            "event": "connected",
            "message": "Connected to VoiceMate Real-Time Event Stream"
        }))
        while True:
            # Keep-alive ping/pong
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        _active_event_subscribers.discard(websocket)
        logger.info("Agent event subscriber disconnected.")
    except Exception as e:
        _active_event_subscribers.discard(websocket)
        logger.warning(f"Event subscriber error: {e}")
