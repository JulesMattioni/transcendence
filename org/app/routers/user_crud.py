from fastapi import APIRouter
from app.services.crud_service import CrudUser
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

_service = CrudUser()
