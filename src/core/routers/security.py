from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis

from src.DB.redis import get_redis


ACCESS_SECRET_KEY = "ee7444aee8d06ca563ec1957c9933826b63ef885611da8152d6448e89793ee14"
REFRESH_SECRET_KEY = "7fd574c66271ed5662037cba0f582efcf25321a3a35d50b2f10ad7a609ac86af"
ALG = "HS256"

ACCESS_EXP_TIME_MIN = 30
REFRESH_EXP_TIME_DAY = 15


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/")


async def create_token(id:int, role:str):
    time = datetime.now()
    access_payload = {
        "sub":str(id),
        "role": role,
        "exp":time + timedelta(minutes=ACCESS_EXP_TIME_MIN),
        "iat":time,
        "type":"access"
    }
    access_token = jwt.encode(access_payload, ACCESS_SECRET_KEY, algorithm=ALG)
    refresh_payload = {
        "sub":str(id),
        "exp":time + timedelta(minutes=REFRESH_EXP_TIME_DAY),
        "iat":time,
        "type":"refresh"
    }
    refresh_token = jwt.encode(refresh_payload, REFRESH_SECRET_KEY, algorithm=ALG)
    return access_token, refresh_token


async def upload_token(id:int, access_token:str, refresh_token:str, db:Redis = Depends(get_redis)):
    await db.set(f"whitelist_access_{access_token}", id, ex=ACCESS_EXP_TIME_MIN * 60)
    await db.set(f"refresh_token_{id}", refresh_token, ex=REFRESH_EXP_TIME_DAY * 24 * 3600)


async def block_token(access_token:str, db:Redis = Depends(get_redis)):
    if not await db.exists(f"whitelist_access_{access_token}"):
        raise HTTPException(
            detail="Invalid access token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    if not await db.exists(f"blacklist_access_{access_token}"):
        raise HTTPException(
            detail="Invalid access token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    id = await db.get(f"whitelist_access_{access_token}")
    time = await db.ttl(f"whitelist_access_{access_token}")
    await db.set(f"blacklist_access_{access_token}", id, ex=time)
    await db.delete(f"whitelist_access_{access_token}")
    await db.delete(f"refresh_token_{id}")
   

async def refresh_tokens(refresh_token:str, db:Redis = Depends(get_redis)):
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=ALG)
        id = payload.get("sub")
        exist_token = db.get(f"refresh_token_{id}")
        if not exist_token:
            raise HTTPException(
                detail="Refresh token expired or logged out",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        if exist_token != refresh_token:
            await db.delete(f"refresh_token_{id}")
            raise HTTPException(
                detail="Token mismatch",
                status_code=status.HTTP_401_UNAUTHORIZED                
                )
        new_access, new_refresh = await create_token(id)
        await upload_token(id, new_access, new_refresh)
        return new_access, new_refresh
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


async def check_access_token(token: str = Depends(oauth2_scheme), db:Redis = Depends(get_redis)):
    if await db.exists(f"blacklist_access_{token}"):
        raise HTTPException(           
            detail="Access token expired or logged out",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    try:
        payload = jwt.decode(token, ACCESS_SECRET_KEY, algorithms=ALG)
        return payload 
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )
    

def get_role(allowed:list[str]):
    async def _check(user:dict = Depends(check_access_token)):
        if user.get("role") not in allowed:
            raise HTTPException(
                detail="Do not have permission to access",
                status_code=status.HTTP_403_FORBIDDEN
            )
        return user
    return _check