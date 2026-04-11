from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.DB.DBconfig import *
from src.DB.schemas import NoteCreate, NoteResponse, NoteUpdate


router = APIRouter(prefix="/note", tags=["note api"])


@router.get("/{id}", response_model=NoteResponse)
async def get_note(id:int, db:AsyncSession = Depends(get_db)):
    note_query = await db.execute(select(Note).where(Note.id == id))
    note = note_query.scalars().first()
    if not note:
        raise HTTPException(
            detail="Not found note with this id",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return note

@router.post("/",response_model=NoteResponse)
async def post_note(data:NoteCreate, db:AsyncSession = Depends(get_db)):
    note_query = await db.execute(select(Note).where(Note.text == data.text))
    note = note_query.scalars().first()
    if note:
        raise HTTPException(
            detail="Bad request, user with this email already exist",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    new_note = Note(**data.model_dump())
    db.add(new_note)
    try:
        await db.commit()
        await db.refresh(new_note)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return new_note


@router.put("/", response_model=NoteResponse)
async def put_note(data:NoteUpdate, db:AsyncSession = Depends(get_db)):
    note_query = await db.execute(select(Note).where(Note.id == data.id))
    note = note_query.scalars().first()
    if not note:
        raise HTTPException(
            detail="Not found note with this id",
            status_code=status.HTTP_404_NOT_FOUND
        )
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)
    try:
        await db.commit()
        await db.refresh(note)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return note


@router.delete("/{id}")
async def delete_note(id:int, db:AsyncSession = Depends(get_db)):
    note_query = await db.execute(select(Note).where(Note.id == id))
    note = note_query.scalars().first()
    if not note:
        raise HTTPException(
            detail="Not found user with this id",
            status_code=status.HTTP_404_NOT_FOUND
        )
    await db.delete(note)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            detail=f"Something goes wrong:{e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
    return None