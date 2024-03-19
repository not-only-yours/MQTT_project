from pydantic import BaseModel, ValidationError
from app.entities.agent_data import AgentData
from typing import List
import json
class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData
