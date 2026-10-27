import asyncio

import certifi
import httpx
import logging
from typing import Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)

async def fetch_paginated_data(
    *,
    log_title: str,
    logger: logging.Logger,
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, str]] = None,
    page_size: int = 5000,
    max_concurrent_requests: int = 5,
) -> List[dict]:
    """
    Generic function to fetch paginated data asynchronously.

    Args:
        *: The `*` enforces keyword-only arguments, meaning all parameters after the * must be explicitly named when calling this function. 
            This improves readability and prevents positional argument errors.
        log_title (str): Custom logging function.
        method (str): HTTP method (e.g., 'GET', 'POST').
        url (str): API endpoint URL.
        headers (Optional[Dict[str, str]]): Headers for the request.
        params (Optional[Dict[str, str]]): Query parameters.
        body (Optional[Dict[str, str]]): Request body.
        page_size (int): Number of results per page.
        max_concurrent_requests (int): Max concurrent API requests.

    Returns:
        List[dict]: Aggregated results from all paginated requests.
    """

    logger.info(f"ASYNC { log_title } - Paginator - Fetching data with config ( page_size: { page_size }, max_concurrent_requests: { max_concurrent_requests } )")

    result: List[dict] = []
    page_number = 0
    fetch_data = True

    async with httpx.AsyncClient(verify=certifi.where()) as client:
        while fetch_data:
            concurrent_requests: List[Coroutine] = []

            for _ in range(max_concurrent_requests):
                request_params = params.copy() if params else {}
                request_params.update({"pageSize": page_size, "pageNumber": page_number})
                concurrent_requests.append(
                    client.request(method, url, headers=headers, params=request_params, json=body)
                )
                page_number += 1

            batched_responses: List[httpx.Response] = await asyncio.gather(*concurrent_requests)

            for response in batched_responses:
                if response.is_error:
                    logger.error(f"ASYNC { log_title } - Paginator - Error fetching data: {response.status_code} - { response.content}")
                    raise ValueError(f"{ log_title } - Paginator - Error fetching data: {response.status_code } - { response.content }")
                data = response.json()
                curr_page = response.request.url.params.get("pageNumber")

                logger.info(f"ASYNC { log_title } - Paginator - Page {curr_page} fetched. Contains {len(data)} records.")
                result.extend(data)

                if len(data) < page_size:
                    fetch_data = False  # Stop fetching if last page reached

    logger.info(f"ASYNC { log_title } - Paginator - Finished fetching data. Total records: {len(result)}")
    return result
