from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from naples.database import get_db

metadatas_router = APIRouter(prefix="/metadatas", tags=["Metadatas"])


@metadatas_router.get("/")
async def get_metadatas(db: Session = Depends(get_db)):
    pass
