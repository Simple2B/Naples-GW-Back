from fastapi import status
from jose import JWTError, jwt
from fastapi import HTTPException
from pydantic import ValidationError

import naples.schemas as s
from naples.utils import get_expire_datatime
from .config import config

CFG = config()

SECRET_KEY = CFG.JWT_SECRET
ACCESS_TOKEN_EXPIRE_MINUTES = CFG.ACCESS_TOKEN_EXPIRE_MINUTES


INVALID_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_access_token(user_id: int) -> str:
    EXPIRE_DATETIME = get_expire_datatime()
    to_encode = s.TokenData(
        user_id=user_id,
        exp=EXPIRE_DATETIME,
    ).model_dump()

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY)

    return encoded_jwt


def create_access_token_exp_datetime(user_id: int) -> s.TokenOut:
    EXPIRE_DATETIME = get_expire_datatime()
    to_encode = s.TokenData(
        user_id=user_id,
        exp=EXPIRE_DATETIME,
    ).model_dump()

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY)

    return s.TokenOut(access_token=encoded_jwt, expire_time=EXPIRE_DATETIME)


def verify_access_token(token: str, credentials_exception) -> s.TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY)
        token_data = s.TokenData.model_validate(payload)
    except ValidationError:
        raise credentials_exception
    except JWTError:
        raise credentials_exception

    return token_data
