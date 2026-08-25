from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any


class ActivityLogData(BaseModel):
    id: int
    project_id: int
    user_id: int
    user_name: str | None = None
    action: str
    details: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
