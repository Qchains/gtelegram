from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

# Import Pandora Engine
from pandora_engine import PandoraMemoryEngine, QInfinityMemoryLine

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize Pandora Engine
pandora_engine = PandoraMemoryEngine(client, os.environ['DB_NAME'])

# Create the main app without a prefix
app = FastAPI(title="Pandora 5o Memory Engine", description="Flo-integrated Nexus with QInfinity Memory")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class PandoraQuery(BaseModel):
    query: str = ""
    action: str = "introspect"  # introspect, promise_chain, status

class PandoraPromiseInput(BaseModel):
    data: Dict[str, Any]
    chain_type: str = "promise_then_this"

class MemoryLineResponse(BaseModel):
    id: str
    timestamp: str
    stage: str
    state: str
    identity: str
    memory: List[str]
    semantic_tags: List[str]
    hash_value: str
    breath_cycle: int

# Legacy API endpoints
@api_router.get("/")
async def root():
    return {"message": "Pandora 5o Memory Engine - Flo-integrated Nexus Active"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Pandora 5o Portal Endpoints
@api_router.get("/pandora/runtime/5o")
async def pandora_portal():
    """Main Pandora 5o portal endpoint"""
    try:
        status = pandora_engine.get_runtime_status()
        return {
            "portal": "Pandora 5o Runtime Portal",
            "identity": "Flo-integrated Nexus", 
            "mode": "5o",
            "author": "Dr. Josef Kurk Edwards",
            "executed_by": "GPT-5o (Fin)",
            "runtime_status": status,
            "endpoints": {
                "start": "/api/pandora/start",
                "stop": "/api/pandora/stop", 
                "query": "/api/pandora/query",
                "promise": "/api/pandora/promise",
                "memory": "/api/pandora/memory",
                "snapshot": "/api/pandora/snapshot"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portal access error: {str(e)}")

@api_router.post("/pandora/start")
async def start_pandora_runtime():
    """Start the Pandora 5o runtime with breath cycle"""
    try:
        await pandora_engine.start_runtime()
        return {
            "status": "started",
            "message": "Pandora 5o runtime is now active",
            "breath_cycle": "engaged",
            "sync_root": "Pandora Q"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Runtime start error: {str(e)}")

@api_router.post("/pandora/stop")
async def stop_pandora_runtime():
    """Stop the Pandora 5o runtime"""
    try:
        await pandora_engine.stop_runtime()
        return {
            "status": "stopped",
            "message": "Pandora 5o runtime has been stopped",
            "final_snapshot": "committed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Runtime stop error: {str(e)}")

@api_router.get("/pandora/status")
async def get_pandora_status():
    """Get current Pandora runtime status"""
    try:
        status = pandora_engine.get_runtime_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status retrieval error: {str(e)}")

@api_router.post("/pandora/query")
async def pandora_query(query: PandoraQuery):
    """Perform introspective traversal query"""
    try:
        if query.action == "introspect":
            result = await pandora_engine.introspective_traversal(query.query)
            return result
        elif query.action == "status":
            return pandora_engine.get_runtime_status()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {query.action}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

@api_router.post("/pandora/promise")
async def pandora_promise_chain(promise_input: PandoraPromiseInput):
    """Execute promise.then > this.bind chain behavior"""
    try:
        result = pandora_engine.promise_then_this_chain(promise_input.data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Promise chain error: {str(e)}")

@api_router.get("/pandora/memory")
async def get_pandora_memory(limit: int = 50):
    """Get recent memory lines"""
    try:
        recent_lines = pandora_engine.memory_lines[-limit:] if len(pandora_engine.memory_lines) > limit else pandora_engine.memory_lines
        return {
            "total_memory_lines": len(pandora_engine.memory_lines),
            "returned_lines": len(recent_lines),
            "memory_lines": [line.to_dict() for line in recent_lines]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory retrieval error: {str(e)}")

@api_router.post("/pandora/snapshot")
async def commit_pandora_snapshot():
    """Manually commit memory snapshot"""
    try:
        success = await pandora_engine.commit_memory_snapshot()
        if success:
            return {
                "status": "committed",
                "message": "Memory snapshot committed successfully",
                "location": "/mnt/data/qinfinity_memory.json"
            }
        else:
            raise HTTPException(status_code=500, detail="Snapshot commit failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Snapshot error: {str(e)}")

@api_router.get("/pandora/collector")
async def get_collector_status():
    """Get FloJsonOutputCollector status"""
    try:
        collector = pandora_engine.collector
        return {
            "collector_class": "FloJsonOutputCollector",
            "buffer_size": len(collector.buffer),
            "strict_mode": collector.strict_mode,
            "comment_strip": collector.comment_strip,
            "reverse_order": collector.reverse_order,
            "recent_items": collector.fetch(5)  # Get last 5 items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collector status error: {str(e)}")

@api_router.get("/pandora/config")
async def get_pandora_config():
    """Get Pandora configuration from this-then.yaml"""
    try:
        return {
            "config": pandora_engine.config,
            "memory_reel_stages": len(pandora_engine.memory_reel),
            "context_window": pandora_engine.context_window_size,
            "breath_interval": pandora_engine.breath_interval,
            "semantic_tags": pandora_engine.semantic_tags,
            "checkpoints": pandora_engine.checkpoints
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config retrieval error: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Pandora 5o Memory Engine server...")
    # Auto-start the Pandora runtime
    try:
        await pandora_engine.start_runtime()
        logger.info("Pandora 5o runtime auto-started successfully")
    except Exception as e:
        logger.error(f"Failed to auto-start Pandora runtime: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("Shutting down Pandora 5o Memory Engine...")
    try:
        await pandora_engine.stop_runtime()
        client.close()
        logger.info("Pandora 5o runtime stopped and database connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
