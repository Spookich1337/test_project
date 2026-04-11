from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.DB.DBconfig import *
from src.DB.schemas import UserCreate, UserResponse, UserUpdate


router = APIRouter(prefix="/user", tags=["user api"])


@router.get("/{id}", response_model=UserResponse)
async def get_user(id:int, db:AsyncSession = Depends(get_db)):
    user_query = await db.execute(select(User).where(User.id == id))
    user = user_query.scalars().first()
    if not user:
        raise HTTPException(
            detail="Not found user with this id",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return user

@router.post("/", response_model=UserResponse)
async def post_user(data:UserCreate, db:AsyncSession = Depends(get_db)):
    user_query = await db.execute(select(User).where(User.email == data.email))
    user = user_query.scalars().first()
    if user:
        raise HTTPException(
            detail="Bad request, user with this email already exist",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    new_user = User(**data.model_dump())
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return new_user


@router.put("/", response_model=UserResponse)
async def put_user(data:UserUpdate, db:AsyncSession = Depends(get_db)):
    user_query = await db.execute(select(User).where(User.id == data.id))
    user = user_query.scalars().first()
    if not user:
        raise HTTPException(
            detail="Not found user with this id",
            status_code=status.HTTP_404_NOT_FOUND
        )
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return user


@router.delete("/{id}")
async def delete_user(id:int, db:AsyncSession = Depends(get_db)):
    user_query = await db.execute(select(User).where(User.id == id))
    user = user_query.scalars().first()
    if not user:
        raise HTTPException(
            detail="Not found user with this id",
            status_code=status.HTTP_404_NOT_FOUND
        )
    await db.delete(user)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return None