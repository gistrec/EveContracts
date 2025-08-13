from typing import Dict, List, Any, Set
from sqlalchemy import delete

from database.db import SessionLocal
from database.models import ContractItem


def upsert_items(region_id: int, items_map: Dict[int, List[Dict[str, Any]]]) -> None:
    """Replace items for the given contracts.

    items_map: {contract_id: [item_dict, ...]}
    """
    with SessionLocal() as session:
        for contract_id, items in items_map.items():
            session.query(ContractItem).filter_by(contract_id=contract_id).delete()
            objects = [
                ContractItem(region_id=region_id, contract_id=contract_id, **item)
                for item in items
            ]
            if objects:
                session.bulk_save_objects(objects)
        session.commit()


def delete_missing_items(region_id: int, seen_ids: Set[int]) -> None:
    """Delete items of contracts in region not present in seen_ids."""
    with SessionLocal() as session:
        stmt = (
            delete(ContractItem)
            .where(ContractItem.region_id == region_id)
            .where(ContractItem.contract_id.notin_(seen_ids))
        )
        session.execute(stmt)
        session.commit()
