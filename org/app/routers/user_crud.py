from fastapi import APIRouter
from app.services.crud_service import CrudUser

router = APIRouter()

_service = CrudUser()
