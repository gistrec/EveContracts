# database/queries/contracts.py

from typing import List, Dict, Any, Set
from sqlalchemy import delete

from database.db import SessionLocal
from database.models import Contract


def get_existing_contracts_by_region(region_id: int) -> Dict[int, Contract]:
    """
    Load all active contracts for the given region from the DB into a dict:
      { contract_id: Contract_obj }
    """
    with SessionLocal() as session:
        rows = session.query(Contract).filter_by(region_id=region_id).all()
        return {
            getattr(contract, "contract_id"): contract for contract in rows
        }


def upsert_contracts(region_id: int, contracts: List[Dict[str, Any]]) -> None:
    """
    Insert new contracts and update changed ones.
    Expects contracts to be a list of dicts with keys matching Contract columns.
    """
    with SessionLocal() as session:
        existing = get_existing_contracts_by_region(region_id)
        to_add = []
        to_update = []

        for data in contracts:
            cid = data["contract_id"]
            obj = existing.get(cid)
            if obj:
                # Compare and update only if something changed
                changed = False
                for col, value in data.items():
                    if getattr(obj, col) != value:
                        setattr(obj, col, value)
                        changed = True
                if changed:
                    to_update.append(obj)
            else:
                # New contract
                to_add.append(Contract(**data))

        if to_add:
            session.bulk_save_objects(to_add)
        # Updates are tracked; a flush is enough
        if to_update:
            session.bulk_save_objects(to_update)

        session.commit()


def delete_missing_contracts(region_id: int, seen_ids: Set[int]) -> None:
    """
    Remove any contracts in the DB for this region not in seen_ids (they've disappeared).
    """
    with SessionLocal() as session:
        stmt = (
            delete(Contract)
            .where(Contract.region_id == region_id)
            .where(Contract.contract_id.notin_(seen_ids))
        )
        session.execute(stmt)
        session.commit()
