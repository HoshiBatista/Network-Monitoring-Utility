from datetime import datetime

from pydantic import BaseModel

from app.models.node import NodeStatus


class StatusLogResponse(BaseModel):
    id: int
    node_id: int
    old_status: NodeStatus
    new_status: NodeStatus
    timestamp: datetime

    model_config = {"from_attributes": True}
