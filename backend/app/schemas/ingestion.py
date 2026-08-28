from pydantic import BaseModel
from app.models.document import IngestionStatus

class IngestionStatusResponse(BaseModel):
    version_id: str
    status: IngestionStatus
    message: str | None = None
