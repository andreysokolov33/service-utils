import httpx
from typing import Optional, Any, Dict
from .context import request_id_ctx_var
import logging

logger = logging.getLogger(__name__)

class TracedHTTPClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
    ):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=headers or {}
        )

    async def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        # Получаем текущий request_id
        request_id = request_id_ctx_var.get()

        # Добавляем request_id в заголовки
        headers = kwargs.get('headers', {})
        headers['X-Request-ID'] = request_id
        kwargs['headers'] = headers

        logger.info(
            f"Making {method} request to {url}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url
            }
        )

        try:
            response = await self.client.request(method, url, **kwargs)
            logger.info(
                f"Received response from {url} with status {response.status_code}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "url": url
                }
            )
            return response
        except Exception as e:
            logger.error(
                f"Error making request to {url}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "url": url
                }
            )
            raise

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("DELETE", url, **kwargs)

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()