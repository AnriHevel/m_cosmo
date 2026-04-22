from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ===== Store =====


class StoreBase(BaseModel):
    store_code: str
    store_type: str
    city: str
    address: str
    full_address: str
    name: Optional[str] = None
    is_active: bool = True


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    store_type: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    full_address: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ===== Scan Request =====

# Фиксированный тип магазина согласно требованиям
FIXED_STORE_TYPE = "М.Косметик"


class ScanStoresRequest(BaseModel):
    city: str
    street: Optional[str] = None
    force_update: bool = False


class StorePreviewItem(BaseModel):
    """Один магазин из результатов preview (ещё не в БД)."""

    store_code: str
    store_type: str = FIXED_STORE_TYPE
    city: str
    address: str
    full_address: str
    name: Optional[str] = None
    exists_in_db: bool = False  # подсветка существующих


class AddSelectedStoresRequest(BaseModel):
    """Добавить выбранные магазины из preview."""

    stores: list[StorePreviewItem]


class SelectStoreRequest(BaseModel):
    city: str
    street: Optional[str] = None
    store_type: str = FIXED_STORE_TYPE
    update_env: bool = True


class DeleteStoresRequest(BaseModel):
    ids: list[str]


# ===== ScanJob =====


class ScanJobResponse(BaseModel):
    id: int
    job_type: str
    store_code: Optional[str] = None
    job_name: Optional[str] = None
    status: str
    progress_percent: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


# ===== Scan Request =====

class ScanStoresRequest(BaseModel):
    city: str
    street: Optional[str] = None
    force_update: bool = False


class StorePreviewItem(BaseModel):
    """Один магазин из результатов preview (ещё не в БД)."""

    store_code: str
    store_type: str = "М.Косметик"
    city: str
    address: str
    full_address: str
    name: Optional[str] = None
    exists_in_db: bool = False  # подсветка существующих


class AddSelectedStoresRequest(BaseModel):
    """Добавить выбранные магазины из preview."""

    stores: list[StorePreviewItem]


class SelectStoreRequest(BaseModel):
    city: str
    street: Optional[str] = None
    store_type: str = "М.Косметик"
    update_env: bool = True


class DeleteStoresRequest(BaseModel):
    ids: list[str]


# ===== ScanJob =====


class ScanJobResponse(BaseModel):
    id: int
    job_type: str
    store_code: Optional[str] = None
    status: str
    progress: int = 0
    progress_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    items_scanned: int = 0
    items_added: int = 0
    items_updated: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    total_stores: int = 0
    current_store_index: int = 0
    current_store_code: Optional[str | int] = None
    current_store_address: Optional[str] = None
    total_categories: int = 0
    current_category_index: int = 0
    current_category_name: Optional[str] = None
    current_category_magnit_id: Optional[int] = None
    current_category_items_total: int = 0
    current_category_items_loaded: int = 0

    model_config = {"from_attributes": True}


# ===== Categories =====


class UpdateCategoriesTrackingRequest(BaseModel):
    """Запрос на обновление отслеживания категорий."""

    category_ids: list[int]
