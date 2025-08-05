import time
import logging
from datetime import datetime, timezone

from api import fetch_public_contracts, fetch_contract_items
from utils.metrics import ExecutionTimer

from database.queries.contracts import get_existing_contracts_by_region, upsert_contracts, delete_missing_contracts


# Constants
TRADE_REGIONS = {
    "Jita": 10000002,
}
SYNC_INTERVAL_SECONDS = 300  # full resync every 5 minutes
BATCH_SIZE = 50  # how many contracts to accumulate before writing


# helper to parse ESI’s ISO8601 with “Z”
def parse_esi_datetime(s: str) -> datetime:
    # ESI dates look like '2025-07-07T10:43:31Z'
    # strip the trailing Z and parse as UTC
    if s is None:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def basic_contract_changed(existing, normalized):
    """
    Compare key fields to decide if the contract was updated.
    existing is the ORM object, normalized is the new dict.
    """
    if existing.title != normalized["title"]:
        return True
    if float(existing.price) != float(normalized["price"]):
        return True
    if int(existing.volume) != int(normalized["volume"]):
        return True
    # you can add more comparisons if needed
    return False


def normalize_contract_basic(contract: dict, region_id: int, now: datetime):
    """
    Extract only the basic fields you need (no items),
    converting date strings into datetime objects.
    """
    return {
        "contract_id": contract["contract_id"],
        "type": contract.get("type", "unknown"),
        "title": contract.get("title", ""),
        "region_id": region_id,
        "collateral": contract.get("collateral"),
        "issuer_id": contract.get("issuer_id"),
        "issuer_corporation_id": contract.get("issuer_corporation_id"),
        "date_issued": parse_esi_datetime(contract["date_issued"]),
        "date_expired": parse_esi_datetime(contract["date_expired"]),
        "days_to_complete": contract.get("days_to_complete", 0),
        "start_location_id": contract.get("start_location_id"),
        "end_location_id": contract.get("end_location_id"),
        "price": contract.get("price", 0.0),
        "reward": contract.get("reward", 0.0),
        "volume": int(contract.get("volume", 0)),
        "last_seen": now,           # datetime, not string
        # created_at/updated_at will be set by the DB defaults, so omit them here
    }


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    region_name = "Jita"
    region_id = TRADE_REGIONS[region_name]

    while True:
        now = datetime.now(timezone.utc)
        logging.info(f"[{region_name}] Starting sync at {now.isoformat()}")

        existing_map = get_existing_contracts_by_region(region_id)  # contract_id -> ORM obj

        seen_ids = set()
        batch = []
        total_new = 0
        total_updated = 0
        total_fetched = 0

        try:
            page = 1
            while True:
                with ExecutionTimer("fetch_page", extra=f"{region_name} page {page}"):
                    contracts, total_pages = fetch_public_contracts(region_id, page=page)

                page_new = 0
                page_updated = 0
                logging.info(f"[{region_name}] fetching page {page}/{total_pages} with {len(contracts)} contracts")

                for c in contracts:
                    contract_id = c["contract_id"]
                    seen_ids.add(contract_id)
                    normalized = normalize_contract_basic(c, region_id, now)

                    # Check if we already have this contract
                    refresh = False

                    existing = existing_map.get(contract_id)
                    if existing is None:
                        page_new += 1
                        total_new += 1
                        refresh = True  # new contract: grab items
                    elif basic_contract_changed(existing, normalized):
                        page_updated += 1
                        total_updated += 1
                        refresh = True  # updated: refresh items

                    if existing and existing.items is None:
                        refresh = True

                    if refresh:
                        try:
                            items = fetch_contract_items(contract_id)
                            normalized["items"] = items
                        except Exception as e:
                            logging.error(f"[{region_name}] Error fetching items for contract {contract_id}: {e}")
                            normalized["items"] = []

                        batch.append(normalized)

                    if len(batch) >= BATCH_SIZE:
                        with ExecutionTimer("upsert_batch", extra=f"{region_name} page {page} size {len(batch)}"):
                            upsert_contracts(region_id, batch)

                        batch.clear()
                        # refresh existing_map so subsequent comparisons see updated state
                        existing_map = get_existing_contracts_by_region(region_id)

                # flush remaining in page chunk
                if batch:
                    with ExecutionTimer("upsert_batch", extra=f"{region_name} page {page} final_flush {len(batch)}"):
                        upsert_contracts(region_id, batch)

                    batch.clear()
                    existing_map = get_existing_contracts_by_region(region_id)

                total_fetched += len(contracts)
                logging.info(
                    f"[{region_name}] page {page}/{total_pages}: "
                    f"fetched={len(contracts)}, new={page_new}, updated={page_updated}"
                )

                if page >= total_pages:
                    break
                page += 1

            # delete contracts that disappeared
            with ExecutionTimer("delete_missing", extra=region_name):
                delete_missing_contracts(region_id, seen_ids)

            logging.info(
                f"[{region_name}] Sync complete. Total fetched: {total_fetched}. "
                f"New: {total_new}, Updated: {total_updated}, Active: {len(seen_ids)}"
            )

        except Exception as e:
            logging.error(f"[{region_name}] error during sync: {e}")

        time.sleep(SYNC_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()