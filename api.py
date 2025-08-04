import time
import logging
from typing import Optional, Tuple, List, Dict, Any

import requests

# --- Configuration ---
ESI_BASE = "https://esi.evetech.net/latest"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "eve-contract-scanner/0.1"
}

# --- Helpers ---
def _sleep_backoff(attempt: int, base: float = 1.5):
    """Exponential backoff sleep."""
    time.sleep(base ** (attempt - 1))


def _safe_get(url: str, params: Optional[Dict[str, Any]] = None, max_attempts: int = 3) -> requests.Response:
    """
    GET with simple retry/backoff policy for transient errors, 429s, and near-exhausted error-limit.
    """
    for attempt in range(1, max_attempts + 1):
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        status = resp.status_code
        remain = resp.headers.get("X-ESI-Error-Limit-Remain")

        # success
        if status == 200:
            return resp

        # retryable situations: 429, 5xx, or error-limit almost exhausted
        if status == 429 or status in (502, 503, 504) or (remain is not None and int(remain) <= 1):
            if attempt == max_attempts:
                break
            logging.warning(
                f"[api] GET {url} returned status={status}, error-limit-remaining={remain}, "
                f"attempt {attempt}/{max_attempts}, backing off..."
            )
            _sleep_backoff(attempt)
            continue

        # non-retryable error: raise immediately
        resp.raise_for_status()

    # last attempt (will raise if bad)
    final = requests.get(url, params=params, headers=HEADERS, timeout=10)
    final.raise_for_status()
    return final


# --- Public API functions ---
def fetch_public_contracts(region_id: int, page: int = 1) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch public contracts for a given region and page.

    Returns:
        contracts: list of contract dicts
        total_pages: int from X-Pages header
    """
    url = f"{ESI_BASE}/contracts/public/{region_id}/"
    resp = _safe_get(url, params={"page": page})
    contracts = resp.json()
    total_pages = int(resp.headers.get("X-Pages", "1"))
    return contracts, total_pages


def fetch_contract_items(contract_id: int) -> List[Dict[str, Any]]:
    """
    Fetch items for a specific public contract.
    """
    url = f"{ESI_BASE}/contracts/public/items/{contract_id}/"
    resp = _safe_get(url)
    return resp.json()
