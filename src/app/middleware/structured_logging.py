from mailbox import Message
from typing import Any, Awaitable, Callable, Coroutine, MutableMapping
import uuid
from fastapi import Request, Response
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction, RequestResponseEndpoint
from starlette.types import ASGIApp


class LogConfig(BaseModel):
    LOGGER_NAME: str = "mycoolapp"
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers: dict = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }


class RouterLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Callable[[MutableMapping[str, Any], Callable[[], Awaitable[MutableMapping[str, Any]]], Callable[[MutableMapping[str, Any]], Awaitable[None]]], Awaitable[None]],
        dispatch: Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]] | None = None
    )-> None:
        super().__init__(app, dispatch)


    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Coroutine[Any, Any, Response]:
        request_id = str(uuid.uuid4())
        logging_dict = {"X-API-REQUEST-ID": request_id}

        await self.set_body(request)
        response, response_dict = await self._log_response(call_next, request, request_id)
        request_dict = await self._log_request(request)
        
        logging_dict["request"] = request_dict
        logging_dict["response"] = response_dict

        self._logger.info(logging_dict)

        return response


    async def set_body(self, request: Request):
        receive_ = await request._receive()

        async def receive() -> Message:
            return receive_ 
        
        request._receive = receive
