from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.exceptions import ItemNotFoundException
from src.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from src.services.item_service import ItemService

router = APIRouter(prefix="/items", tags=["Items"])


@router.get("/", response_model=List[ItemResponse], summary="Lấy danh sách Items")
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return ItemService.get_all(db, skip=skip, limit=limit)


@router.get("/{item_id}", response_model=ItemResponse, summary="Lấy thông tin Item theo ID")
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = ItemService.get_by_id(db, item_id=item_id)
    if not item:
        raise ItemNotFoundException(item_id=item_id)
    return item


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, summary="Tạo mới Item")
def create_item(item_in: ItemCreate, db: Session = Depends(get_db)):
    return ItemService.create(db, item_in=item_in)


@router.put("/{item_id}", response_model=ItemResponse, summary="Cập nhật Item")
def update_item(item_id: int, item_in: ItemUpdate, db: Session = Depends(get_db)):
    updated_item = ItemService.update(db, item_id=item_id, item_in=item_in)
    if not updated_item:
        raise ItemNotFoundException(item_id=item_id)
    return updated_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xóa Item")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    success = ItemService.delete(db, item_id=item_id)
    if not success:
        raise ItemNotFoundException(item_id=item_id)
    return None
