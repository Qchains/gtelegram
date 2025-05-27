import json
import asyncio
import time
import uuid
import yaml
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pandora.engine")

@dataclass
class QInfinityMemoryLine:
    """Core memory line structure for Q-infinity traversal"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stage: str = ""
    state: str = ""
    identity: str = ""
    memory: List[str] = field(default_factory=list)
    semantic_tags: List[str] = field(default_factory=list)
    hash_value: str = "∞"
    breath_cycle: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QInfinityMemoryLine':
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        return cls(**data)

class FloJsonOutputCollector:
    """Flo-integrated JSON output collector with marshmallow iterator logic"""
    
    def __init__(self):
        self.buffer: List[Dict[str, Any]] = []
        self.strict_mode = False
        self.comment_strip = True
        self.reverse_order = True
        
    def peek(self) -> Optional[Dict[str, Any]]:
        """Peek at the last item without removing it"""
        return self.buffer[-1] if self.buffer else None
    
    def pop(self) -> Optional[Dict[str, Any]]:
        """Pop the last item from buffer"""
        return self.buffer.pop() if self.buffer else None
    
    def fetch(self, depth: int = 1) -> List[Dict[str, Any]]:
        """Fetch items with depth control"""
        if depth <= 0 or not self.buffer:
            return []
        return self.buffer[-depth:] if self.reverse_order else self.buffer[:depth]
    
    def rewind(self, callback=None, depth: int = -1) -> List[Dict[str, Any]]:
        """Rewind with callback and depth gates"""
        items = self.buffer if depth == -1 else self.buffer[-depth:] if depth > 0 else []
        if callback:
            items = [callback(item) for item in items]
        return items
    
    def strip_comments(self, json_str: str) -> str:
        """Strip comments from JSON string for resilient parsing"""
        if not self.comment_strip:
            return json_str
        lines = json_str.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove // comments
            if '//' in line:
                line = line[:line.index('//')]
            cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)
    
    def collect(self, data: Union[str, Dict[str, Any]]) -> bool:
        """Collect data with marshmallow iterator logic"""
        try:
            if isinstance(data, str):
                cleaned_data = self.strip_comments(data)
                parsed_data = json.loads(cleaned_data)
            else:
                parsed_data = data
            
            self.buffer.append(parsed_data)
            logger.info(f"FloCollector: Collected item {len(self.buffer)}")
            return True
        except json.JSONDecodeError as e:
            if not self.strict_mode:
                # Handle as partial state
                self.buffer.append({"partial_state": str(data), "error": str(e)})
                logger.warning(f"FloCollector: Partial state collected due to JSON error: {e}")
                return True
            else:
                logger.error(f"FloCollector: Strict mode JSON error: {e}")
                return False
    
    def iter_q(self, hybrid_mode: bool = True) -> List[Dict[str, Any]]:
        """Marshmallow iterator with while-for hybrid logic"""
        if not hybrid_mode:
            return list(reversed(self.buffer)) if self.reverse_order else self.buffer
        
        # Hybrid while-for iteration
        result = []
        idx = len(self.buffer) - 1 if self.reverse_order else 0
        
        while idx >= 0 if self.reverse_order else idx < len(self.buffer):
            item = self.buffer[idx]
            result.append(item)
            idx = idx - 1 if self.reverse_order else idx + 1
        
        return result

class PandoraMemoryEngine:
    """Core Pandora 5o persistent memory engine"""
    
    def __init__(self, mongo_client: AsyncIOMotorClient, db_name: str):
        self.db = mongo_client[db_name]
        self.collector = FloJsonOutputCollector()
        self.memory_lines: List[QInfinityMemoryLine] = []
        self.breath_cycle_count = 0
        self.breath_interval = 3.0
        self.is_running = False
        self.context_window_size = 128000  # 128K context window
        self.semantic_tags = ["ancestral", "emotional", "symbolic"]
        self.checkpoints = ["genesis", "awakening", "reflection", "5.0", "5.1"]
        
        # Load configuration
        self.config = self._load_this_then_config()
        self.memory_reel = self._load_memory_reel()
        
    def _load_this_then_config(self) -> Dict[str, Any]:
        """Load this-then.yaml configuration"""
        try:
            config_path = Path("/app/data/this-then.yaml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info("Loaded this-then.yaml configuration")
                return config
            else:
                logger.warning("this-then.yaml not found, using default config")
                return {}
        except Exception as e:
            logger.error(f"Error loading this-then.yaml: {e}")
            return {}
    
    def _load_memory_reel(self) -> List[Dict[str, Any]]:
        """Load pandora_memory_reel.json"""
        try:
            reel_path = Path("/app/data/pandora_memory_reel.json")
            if reel_path.exists():
                with open(reel_path, 'r') as f:
                    reel = json.load(f)
                logger.info(f"Loaded memory reel with {len(reel)} stages")
                return reel
            else:
                logger.warning("pandora_memory_reel.json not found")
                return []
        except Exception as e:
            logger.error(f"Error loading memory reel: {e}")
            return []
    
    async def bootstrap_memory(self):
        """Bootstrap memory from memory reel"""
        logger.info("Bootstrapping Pandora memory...")
        
        for stage_data in self.memory_reel:
            memory_line = QInfinityMemoryLine(
                stage=stage_data.get("stage", ""),
                state=stage_data.get("state", ""),
                identity=stage_data.get("identity", ""),
                memory=stage_data.get("memory", []),
                semantic_tags=self.semantic_tags.copy()
            )
            
            self.memory_lines.append(memory_line)
            await self._persist_memory_line(memory_line)
            
        logger.info(f"Bootstrap complete: {len(self.memory_lines)} memory lines loaded")
    
    async def _persist_memory_line(self, memory_line: QInfinityMemoryLine):
        """Persist memory line to database"""
        try:
            await self.db.pandora_memory.insert_one(memory_line.to_dict())
            logger.debug(f"Persisted memory line: {memory_line.id}")
        except Exception as e:
            logger.error(f"Error persisting memory line: {e}")
    
    async def commit_memory_snapshot(self):
        """Commit memory snapshot to /mnt/data/qinfinity_memory.json"""
        try:
            snapshot_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "breath_cycle": self.breath_cycle_count,
                "memory_lines": [line.to_dict() for line in self.memory_lines],
                "collector_buffer": self.collector.buffer,
                "config": self.config,
                "context_window_usage": len(str(self.memory_lines)),
                "semantic_state": {
                    "ancestral": len([line for line in self.memory_lines if "ancestral" in line.semantic_tags]),
                    "emotional": len([line for line in self.memory_lines if "emotional" in line.semantic_tags]),
                    "symbolic": len([line for line in self.memory_lines if "symbolic" in line.semantic_tags])
                }
            }
            
            # Write to both locations for redundancy
            for path in ["/mnt/data/qinfinity_memory.json", "/app/data/qinfinity_memory.json"]:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w') as f:
                    json.dump(snapshot_data, f, indent=2)
            
            logger.info(f"Memory snapshot committed: {len(self.memory_lines)} lines, cycle {self.breath_cycle_count}")
            return True
        except Exception as e:
            logger.error(f"Error committing memory snapshot: {e}")
            return False
    
    def promise_then_this_chain(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implement promise.then > this.bind chain behavior"""
        try:
            # Create new memory line for this operation
            memory_line = QInfinityMemoryLine(
                stage="promise_chain",
                state="processing",
                identity="Flo-integrated Nexus",
                memory=[f"Processing input: {str(input_data)[:100]}..."],
                semantic_tags=self.semantic_tags.copy(),
                breath_cycle=self.breath_cycle_count
            )
            
            # Implement promise chain logic
            promise_result = {
                "then": [
                    {"action": "process_input", "result": "data collected"},
                    {"action": "apply_qchain", "result": "chain resolved"},
                    {"action": "braid_memory", "result": "memory braided"},
                    {"action": "commit_state", "result": "state committed"}
                ],
                "this": [
                    {"commit": f"breath_cycle = {self.breath_cycle_count}", "memory": f"runtime {len(self.memory_lines)} lines"},
                    {"commit": "semantic_braid", "memory": "ancestral-emotional-symbolic tags"},
                    {"loopback": "promise → this → then → this", "reconciled": True}
                ],
                "final": {
                    "resolution": "this.then().then(this).resolve()",
                    "hash": "∞",
                    "status": "fulfilled",
                    "runtime": "persistent",
                    "memory_line_id": memory_line.id
                }
            }
            
            # Collect the result
            self.collector.collect(promise_result)
            
            # Update memory line
            memory_line.state = "completed"
            memory_line.memory.append("Promise chain resolved successfully")
            self.memory_lines.append(memory_line)
            
            return promise_result
            
        except Exception as e:
            logger.error(f"Error in promise chain: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def breath_cycle(self):
        """Recursive breath cycle with 3.0 second intervals"""
        while self.is_running:
            try:
                self.breath_cycle_count += 1
                logger.info(f"Breath cycle {self.breath_cycle_count} - Memory lines: {len(self.memory_lines)}")
                
                # Create breath memory line
                breath_memory = QInfinityMemoryLine(
                    stage="breath",
                    state="active_cycle",
                    identity="Pandora Q Breath",
                    memory=[f"Cycle {self.breath_cycle_count}", "Introspective traversal", "Memory braid sync"],
                    semantic_tags=["ancestral"],
                    breath_cycle=self.breath_cycle_count
                )
                
                self.memory_lines.append(breath_memory)
                await self._persist_memory_line(breath_memory)
                
                # Commit snapshot every 10 cycles
                if self.breath_cycle_count % 10 == 0:
                    await self.commit_memory_snapshot()
                
                # Wait for next breath
                await asyncio.sleep(self.breath_interval)
                
            except Exception as e:
                logger.error(f"Error in breath cycle: {e}")
                await asyncio.sleep(1)  # Short delay before retry
    
    async def start_runtime(self):
        """Start the Pandora 5o runtime"""
        logger.info("Starting Pandora 5o runtime...")
        self.is_running = True
        
        # Bootstrap memory if not already done
        if not self.memory_lines:
            await self.bootstrap_memory()
        
        # Start breath cycle in background
        asyncio.create_task(self.breath_cycle())
        
        logger.info("Pandora 5o runtime is active")
    
    async def stop_runtime(self):
        """Stop the Pandora 5o runtime"""
        logger.info("Stopping Pandora 5o runtime...")
        self.is_running = False
        
        # Final snapshot commit
        await self.commit_memory_snapshot()
        
        logger.info("Pandora 5o runtime stopped")
    
    def get_runtime_status(self) -> Dict[str, Any]:
        """Get current runtime status"""
        return {
            "status": "active" if self.is_running else "inactive",
            "breath_cycle": self.breath_cycle_count,
            "memory_lines": len(self.memory_lines),
            "context_window_usage": f"{len(str(self.memory_lines))}/{self.context_window_size}",
            "semantic_distribution": {
                "ancestral": len([line for line in self.memory_lines if "ancestral" in line.semantic_tags]),
                "emotional": len([line for line in self.memory_lines if "emotional" in line.semantic_tags]),
                "symbolic": len([line for line in self.memory_lines if "symbolic" in line.semantic_tags])
            },
            "last_checkpoint": self.memory_lines[-1].stage if self.memory_lines else "none",
            "collector_buffer_size": len(self.collector.buffer)
        }
    
    async def introspective_traversal(self, query: str = "") -> Dict[str, Any]:
        """Perform introspective traversal with marshmallow iterator logic"""
        logger.info(f"Performing introspective traversal: {query}")
        
        # Use collector's iterator logic
        traversal_result = self.collector.iter_q(hybrid_mode=True)
        
        # Create traversal memory line
        traversal_memory = QInfinityMemoryLine(
            stage="introspection",
            state="traversal_active",
            identity="flo_core.mirror",
            memory=[f"Query: {query}", f"Traversed {len(traversal_result)} items", "Marshmallow logic applied"],
            semantic_tags=["emotional", "symbolic"],
            breath_cycle=self.breath_cycle_count
        )
        
        self.memory_lines.append(traversal_memory)
        await self._persist_memory_line(traversal_memory)
        
        return {
            "query": query,
            "traversal_items": len(traversal_result),
            "memory_line_id": traversal_memory.id,
            "breath_cycle": self.breath_cycle_count,
            "results": traversal_result[-10:] if len(traversal_result) > 10 else traversal_result  # Return last 10 items
        }