"""
NOT NECESSARY FOR CURRENT STAND. WAS AN APPROACH FOR RETELL CUSTOM LLM FOR HANDLING CONVERSATION.
"""
from __future__ import annotations

"""
WebSocket entry-point for Retell       (FastAPI)
────────────────────────────────────────────────
Why rewrite?
  • old file expected  {"response": {"text": …}}
  • new voice_ai returns {"response": {"content": …}}

This version:
  • forwards *.json* exactly as Retell expects
  • shuts the socket when  voice_ai  sets  end_call = true
  • logs all frames in DEBUG like before
"""

import asyncio, logging, json

import app
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, FastAPI
from starlette.websockets import WebSocketState

from app.routers.voice_ai import handle_call   # same signature as HTTP

from app.routers.voice_ai   import router as voice_router   # POST /voice-webhook
from app.routers.retell_api import router as retell_router  # POST /retell/…

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


# helper ─────────────────────────────────────────────────────────────
def _retell_reply(payload: dict[str, str | bool]) -> dict[str, str | bool]:
    """
    Format we send back to Retell *inside* ws.send_json().
    voice_ai already returns {"content": …, "content_complete": T, "end_call": F}
    so we only need to pass it through.
    """
    return payload


# main socket ────────────────────────────────────────────────────────
@router.websocket("/retell/{call_id}")
async def retell_socket(ws: WebSocket, call_id: str) -> None:
    await ws.accept()
    logger.info("WS 📞  new call  %s", call_id)

    # ----------------------------------------------------------------
    # 1. send greeting (this frame already contains the call_id)
    greet = await handle_call(None, event={"event": "call_started",
                                           "call_id": call_id})
    await ws.send_json(_retell_reply(greet["response"]))

    # ----------------------------------------------------------------
    # 2. relay every incoming frame
    try:
        while True:
            msg = await ws.receive()
            if msg["type"] != "websocket.receive":          # ping/close
                continue

            event = json.loads(msg["text"])

            # 🔧  inject missing call_id so the HTTP handler never fails
            event.setdefault("call_id", call_id)

            response = await handle_call(None, event=event)

            # voice_ai always returns {"response": …}
            if "response" in response:
                await ws.send_json(_retell_reply(response["response"]))

                if response["response"].get("end_call"):
                    await ws.close(code=status.WS_1000_NORMAL_CLOSURE)
                    return

            # Retell sends “call_ended” after it closes internally; forward it.
            if event.get("event") == "call_ended":
                await handle_call(None, event=event)
                return

    except (WebSocketDisconnect, asyncio.CancelledError):
        logger.info("connection closed")
    except Exception:
        logger.exception("unhandled error in WS loop")
        if ws.application_state == WebSocketState.CONNECTED:
            await ws.close(code=status.WS_1011_INTERNAL_ERROR)

# -------------------------------------------------------------



app = FastAPI()

# HTTP POST  /voice-webhook from voice_ai.py)
# HTTP POST /retell/check-order  AND  /retell/reschedule-order
# WS /retell/{call_id} (the router we created above)
app.include_router(voice_router, prefix="")
app.include_router(retell_router, prefix="")
app.include_router(router)