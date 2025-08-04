class BaseEnum:
    @classmethod
    def values(cls):
        return [
            value for key, value in vars(cls).items()
            if not key.startswith("__") and isinstance(value, str)
        ]

class ContractType(BaseEnum):
    UNKNOWN       = 'unknown'
    ITEM_EXCHANGE = 'item_exchange'
    AUCTION       = 'auction'
    COURIER       = 'courier'
    LOAN          = 'loan'
