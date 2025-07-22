from datetime import datetime
from pydantic import BaseModel


class TokenData(BaseModel):
    token: str
    exp: datetime
