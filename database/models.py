from sqlalchemy import Column, String, Integer, DateTime, BigInteger, \
    Enum, Numeric, JSON, Index, func
from sqlalchemy.orm import declarative_base

from database.enums import ContractType


class BaseModel:
    def to_dict(self):
        exclude_fields = ("access_token", "refresh_token")
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns  # type: ignore[attr-defined]
            if column.name not in exclude_fields
        }


Base = declarative_base(cls=BaseModel)


# Contract model for public contracts in EVE Online
# https://developers.eveonline.com/api-explorer#/operations/GetContractsPublicRegionId
class Contract(Base):
    __tablename__ = "contracts"

    contract_id = Column(BigInteger, primary_key=True, autoincrement=False)

    type = Column(Enum(*ContractType.values()), nullable=False)

    title = Column(String(126), nullable=False, comment="Title of the contract")

    region_id             = Column(BigInteger, nullable=False, comment="An EVE region id")
    issuer_id             = Column(BigInteger, nullable=False, comment="Character ID for the issuer")
    issuer_corporation_id = Column(BigInteger, nullable=False, comment="Character's corporation ID for the issuer")

    # Dates
    date_issued      = Column(DateTime,   nullable=False, comment="Creation date of the contract")
    date_expired     = Column(DateTime,   nullable=False, comment="Expiration date of the contract")
    days_to_complete = Column(BigInteger, nullable=False, comment="Number of days to perform the contract")

    # Couriers contracts data
    start_location_id = Column(BigInteger, nullable=False, comment="Start location ID (for Couriers contract)")
    end_location_id   = Column(BigInteger, nullable=False, comment="End location ID (for Couriers contract)")

    collateral        = Column(Numeric(18, 2), nullable=False, comment="Collateral price (for Couriers only)")
    reward            = Column(Numeric(18, 2), nullable=False, comment="Remuneration for contract (for Couriers only)")

    # Additional contract data
    buyout = Column(Numeric(18, 2), nullable=False, comment="Buyout price (for Auctions only)")
    price  = Column(Numeric(18, 2), nullable=False, comment="Price of contract (for ItemsExchange and Auctions)")
    volume = Column(Integer,        nullable=False, comment="Volume of items in the contract")

    # Items in the contract
    items        = Column(JSON, nullable=True)
    raw_contract = Column(JSON, nullable=True)

    # Additional metadata
    last_seen  = Column(DateTime, nullable=False, comment="Last time this contract was seen via API")

    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="Creation timestamp")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="Last update timestamp")

    __table_args__ = (
        Index("idx_expiration", "date_expired"),
        Index("idx_issuer", "issuer_id"),
        Index("idx_region_last_seen", "region_id", "last_seen"),
    )
