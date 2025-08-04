import time
import logging
from datetime import datetime, timezone

from api import fetch_public_contracts  # returns (contracts_list, total_pages)
from database.queries.contracts import (
    get_existing_contracts_by_region,
    upsert_contracts,
    delete_missing_contracts,
)

# Constants
TRADE_REGIONS = {
    "Jita": 10000002,
}
SYNC_INTERVAL_SECONDS = 300  # full resync every 5 minutes
BATCH_SIZE = 1000  # how many contracts to accumulate before writing


# helper to parse ESI’s ISO8601 with “Z”
def parse_esi_datetime(s: str) -> datetime:
    # ESI dates look like '2025-07-07T10:43:31Z'
    # strip the trailing Z and parse as UTC
    if s is None:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


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

        # Load existing snapshot from DB once
        existing_map = get_existing_contracts_by_region(region_id)  # {contract_id: ORM obj}

        seen_ids = set()
        batch = []
        total_fetched = 0
        new_count = 0
        updated_count = 0

        try:
            page = 1
            while True:
                contracts, total_pages = fetch_public_contracts(region_id, page=page)
                logging.info(f"[{region_name}] fetched page {page}/{total_pages} with {len(contracts)} contracts")
                total_fetched += len(contracts)

                for c in contracts:
                    cid = c["contract_id"]
                    seen_ids.add(cid)
                    normalized = normalize_contract_basic(c, region_id, now)

                    # Determine if new or updated for logging heuristic
                    existing = existing_map.get(cid)
                    if existing is None:
                        new_count += 1
                    else:
                        # naive comparison: check if price or volume changed
                        if (
                            str(existing.price) != str(normalized["price"])
                            or existing.volume != normalized["volume"]
                            or existing.title != normalized["title"]
                        ):
                            updated_count += 1

                    batch.append(normalized)

                    if len(batch) >= BATCH_SIZE:
                        upsert_contracts(region_id, batch)
                        batch.clear()

                if page >= total_pages:
                    break
                page += 1

            if batch:
                upsert_contracts(region_id, batch)
                batch.clear()

            # Remove disappeared contracts
            delete_missing_contracts(region_id, seen_ids)

            logging.info(
                f"[{region_name}] Sync done. Total fetched: {total_fetched}. "
                f"New: {new_count}, Updated: {updated_count}, Active remaining: {len(seen_ids)}"
            )

        except Exception as e:
            logging.error(f"[{region_name}] error during sync: {e}")

        time.sleep(SYNC_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
