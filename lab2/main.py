from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Set
from pydantic import BaseModel
import uvicorn
import json
import config

# SQLAlchemy setup
DATABASE_URL = f"postgresql+psycopg2://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define the ProcessedAgentData table
processed_agent_data = Table(
    "processed_agent_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)

# FastAPI models
class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float

class GpsData(BaseModel):
    latitude: float
    longitude: float

class AgentData(BaseModel):
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime

    @classmethod
    def check_timestamp(cls, value):
        if value is None:
            return None

        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError("Invalid timestamp format. Expected ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).")

class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData

# Database model
class ProcessedAgentDataInDB(BaseModel):
    id: int
    road_state: str
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI app setup
app = FastAPI()

# WebSocket subscriptions
subscriptions: Set[WebSocket] = set()

# FastAPI WebSocket endpoint
@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    subscriptions.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions.remove(websocket)

# Function to send data to subscribed users
async def send_data_to_subscribers(data):
    for websocket in subscriptions:
        await websocket.send_json(json.dumps(data))

# CRUD operations
@app.post("/processed_agent_data/")
async def create_processed_agent_data(data: List[ProcessedAgentData]):
    db = SessionLocal()
    try:
        for item in data:
            agent_data = item.agent_data
            db.execute(processed_agent_data.insert().values(
                road_state=item.road_state,
                x=agent_data.accelerometer.x,
                y=agent_data.accelerometer.y,
                z=agent_data.accelerometer.z,
                latitude=agent_data.gps.latitude,
                longitude=agent_data.gps.longitude,
                timestamp=agent_data.timestamp
            ))
        db.commit()

        return Response(content="OK", status_code=200)
    finally:
        db.close()

    await send_data_to_subscribers(data)

# Helper function to get processed agent data by ID
def get_processed_agent_data(db, processed_agent_data_id: int):
    result = db.execute(processed_agent_data.select().where(processed_agent_data.c.id == processed_agent_data_id)).first()
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result

@app.get("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def read_processed_agent_data(processed_agent_data_id: int):
    db = SessionLocal()
    try:
        return get_processed_agent_data(db, processed_agent_data_id)
    finally:
        db.close()

@app.get("/processed_agent_data/", response_model=List[ProcessedAgentDataInDB])
def list_processed_agent_data():
    db = SessionLocal()
    try:
        result = db.execute(processed_agent_data.select()).fetchall()
        return result
    finally:
        db.close()

@app.put("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def update_processed_agent_data(processed_agent_data_id: int, data: ProcessedAgentData):
    db = SessionLocal()
    try:
        update_values = {
            "road_state": data.road_state,
            "x": data.agent_data.accelerometer.x,
            "y": data.agent_data.accelerometer.y,
            "z": data.agent_data.accelerometer.z,
            "latitude": data.agent_data.gps.latitude,
            "longitude": data.agent_data.gps.longitude,
            "timestamp": data.agent_data.timestamp
        }
        db.execute(processed_agent_data.update().where(processed_agent_data.c.id == processed_agent_data_id).values(**update_values))
        db.commit()
        return get_processed_agent_data(db, processed_agent_data_id)
    finally:
        db.close()

@app.delete("/processed_agent_data/{processed_agent_data_id}")
def delete_processed_agent_data(processed_agent_data_id: int):
    db = SessionLocal()
    try:
        result = db.execute(processed_agent_data.delete().where(processed_agent_data.c.id == processed_agent_data_id))
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Item deleted successfully"}
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
