from datetime import datetime

from pydantic import BaseModel, Field

from app.models.node import NodeStatus


class NodeCreate(BaseModel):
    address: str = Field(..., min_length=1, max_length=255, description="IP address or hostname")
    port: int | None = Field(None, ge=1, le=65535, description="TCP port to probe (optional)")


class NodeUpdate(BaseModel):
    address: str | None = Field(None, min_length=1, max_length=255)
    port: int | None = Field(None, ge=1, le=65535)


class NodeResponse(BaseModel):
    id: int
    address: str
    port: int | None
    last_status: NodeStatus
    last_latency: float | None
    last_check_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
