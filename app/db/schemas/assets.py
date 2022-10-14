from pydantic import BaseModel
import typing as t


class AddressList(BaseModel):
    addresses: t.List[str]
