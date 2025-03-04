from datetime import datetime
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    exp: datetime


class TokenOut(Token):
    expire_time: datetime


class Auth(BaseModel):
    email: str
    password: str
