import json, logging
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request

logger = logging.getLogger("retell")
logger.setLevel(logging.INFO)

async def _reuse_body(request: Request, body: bytes):
    async def receive():
        return {"type": "http.request", "body": body}
    request._receive = receive           # monkey-patch so downstream can read
    return request

async def raw_logger(request: Request, call_next):
    body = await request.body()          # <-- raw bytes
    logger.debug(
        "<<< %s %s  headers=%s  raw=%s",
        request.method,
        request.url.path,
        dict(request.headers),
        body.decode(errors="ignore"),
    )
    request = await _reuse_body(request, body)
    response = await call_next(request)
    logger.debug(">>> %s  status=%s", request.url.path, response.status_code)
    return response

class BodyLogMiddleware:
    """
    Log *every* HTTP request body **before** FastAPI validation.
    Handy to debug 404 / 422 from Retell.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req = Request(scope, receive=receive)
        raw = await req.body()                    # bytes
        try:
            pretty = json.loads(raw or b"{}")
        except Exception:
            pretty = raw.decode(errors="ignore")

        logger.info("⇢ %s %s  body=%s", req.method, req.url.path, pretty)

        async def _receive() -> dict:             # feed body back into ASGI flow
            return {"type": "http.request", "body": raw, "more_body": False}

        await self.app(scope, _receive, send)