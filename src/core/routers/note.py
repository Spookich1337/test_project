from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.DB.DBconfig import *
from src.DB.schemas import NoteCreate, NoteResponse, NoteUpdate, NoteList
from .security import get_role, check_access_token


router = APIRouter(prefix="/notes", tags=["note api"])


@router.get("/", response_model=NoteList)
async def get_notes_list(size:int, page:int, role:str = Depends(get_role(["admin", "user"])), db:AsyncSession = Depends(get_db)):
    if role == "user":
        notes_query = await db.execute(select(Note).where(Note.for_admin != True).order_by(Note.id).limit(size).offset((page-1)*size))
    else:
        notes_query = await db.execute(select(Note).order_by(Note.id).limit(size).offset((page-1)*size))
    notes = notes_query.scalars().all()
    count = len(notes)
    return {
        "count":count,
        "notes":notes
    }


@router.get("/{id}", response_model=NoteResponse)
async def get_note(id:int, role:str = Depends(get_role(["admin", "user"])), db:AsyncSession = Depends(get_db)):
    note_query = await db.execute(select(Note).where(Note.id == id))
    note = note_query.scalars().first()
    if not note:
        raise HTTPException(
            detail="Not found note with this id",
            status_code=status.HTTP_404_NOT_FOUND
        )
    if (note.for_admin == True) and (role != "admin"):
        raise HTTPException(
            detail="Do not have permission to access",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return note


@router.post("/",response_model=NoteResponse)
async def post_note(data:NoteCreate, user:dict = Depends(check_access_token), db:AsyncSession = Depends(get_db)):
    note_query = await db.execute(select(Note).where(Note.text == data.text))
    note = note_query.scalars().first()
    if note:
        raise HTTPException(
            detail="Bad request, note with this text already exist",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    if data.user_id != int(user.get("sub")):
        raise HTTPException(
            detail="The author's ID does not match the user's ID.",
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
async def put_note(data:NoteUpdate, user:dict = Depends(check_access_token), db:AsyncSession = Depends(get_db)):
    note_query = await db.execute(select(Note).where(Note.id == data.id))
    note = note_query.scalars().first()
    if not note:
        raise HTTPException(
            detail="Not found note with this id",
            status_code=status.HTTP_404_NOT_FOUND
        )
    if note.user_id != int(user.get("sub")) and user.get("role") != "admin":
        raise HTTPException(
            detail="The author's ID does not match the user's ID.",
            status_code=status.HTTP_400_BAD_REQUEST
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


@router.delete("/")
async def delete_note(id:int, user:dict = Depends(check_access_token), db:AsyncSession = Depends(get_db)):
    note_query = await db.execute(select(Note).where(Note.id == id))
    note = note_query.scalars().first()
    if not note:
        raise HTTPException(
            detail="Not found user with this id",
            status_code=status.HTTP_404_NOT_FOUND
        )
    if note.user_id != int(user.get("sub")) and user.get("role") != "admin":
        raise HTTPException(
            detail="The author's ID does not match the user's ID.",
            status_code=status.HTTP_400_BAD_REQUEST
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