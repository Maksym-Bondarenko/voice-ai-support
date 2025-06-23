import logging, sys

from fastapi import FastAPI, Request
from fastapi.logger import logger

from app.log_middleware import BodyLogMiddleware, raw_logger
from app.routers import public_api
from app.routers.retell_api import router as retell_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stdout,
)

app = FastAPI(title="Delivery-Rescheduler API")
app.add_middleware(BodyLogMiddleware)
app.middleware("http")(raw_logger)

# register all Retell HTTP endpoints
app.include_router(retell_router)
# for tests
app.include_router(public_api.router)

# simple health check
@app.get("/")
def root():
    return {"status": "up"}

# dump routes at startup
for r in app.router.routes:
    if hasattr(r, "path"):
        logger.info("route -->  %s  %s", ", ".join(r.methods), r.path)

# for debug, logging
log = logging.getLogger("retell")

@app.middleware("http")
async def dump_request(request: Request, call_next):
    body = await request.body()
    log.info("<<< %s %s  headers=%s  raw=%s",
             request.method, request.url.path,
             dict(request.headers), body.decode(errors="ignore"))
    # body has been consumed – put it back so downstream can read it again
    async def receive():
        return {"type": "http.request", "body": body}
    request._receive = receive          # monkey-patch
    response = await call_next(request)
    log.info(">>> %s  status=%s", request.url.path, response.status_code)
    return response