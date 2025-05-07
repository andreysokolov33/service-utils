from fastapi import FastAPI
from service_utils import setup_logger
from service_utils.middleware import RequestIDMiddleware, TimingMiddleware
from service_utils.context import request_id_ctx_var

# Настраиваем логгер
logger = setup_logger("example_service")

app = FastAPI()

# Важен порядок middleware!
app.add_middleware(TimingMiddleware, logger=logger)
app.add_middleware(RequestIDMiddleware)

@app.get("/")
async def root():
    logger.info(
        "Processing root endpoint",
        extra={"request_id": request_id_ctx_var.get()}
    )
    return {"message": "Hello World", "request_id": request_id_ctx_var.get()}

@app.get("/slow")
async def slow():
    import time
    time.sleep(2)
    logger.info(
        "Processing slow endpoint",
        extra={"request_id": request_id_ctx_var.get()}
    )
    return {"message": "Slow response", "request_id": request_id_ctx_var.get()}