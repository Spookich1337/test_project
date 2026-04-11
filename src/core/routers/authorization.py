from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.DB.schemas import UserBase
from src.DB.DBconfig import *


from .security import *


router = APIRouter(prefix="/auth", tags=["authorization api"])


@router.get("/")
async def author_user(data:UserBase, db:AsyncSession = Depends(get_db)):
    user_query = await db.execute(select(User).where(User.email == data.email))
    exist_user = user_query.scalars().first()
    if not exist_user:
        raise HTTPException(
            detail="Invalid email",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    if exist_user.password != data.password:
        raise HTTPException(
            detail="inavlid password",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    access_token, refresh_token = await create_token(exist_user.id, exist_user.role)
    await upload_token(exist_user.id, access_token, refresh_token)
    Response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=REFRESH_EXP_TIME_DAY
    )
    return {
        "access_token":access_token
    }
    

@router.put("/refresh")
async def refresh_author(refresh:str = Cookie(())):
    if not refresh:
        raise HTTPException(
            detail="Cant find refresh token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    new_access, new_refresh = await refresh_tokens(refresh)
    Response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        samesite="lax",
        max_age=REFRESH_EXP_TIME_DAY
    )
    return {
        "access_token":new_access
    }


@router.delete("/logout")
async def log_out_token(token:str = Depends(oauth2_scheme)):
    await block_token(token)
    return None