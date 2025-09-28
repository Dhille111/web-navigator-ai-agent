"""
Session memory system for maintaining context and task history
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Single memory entry"""
    id: str
    instruction: str
    result: Dict[str, Any]
    timestamp: datetime
    task_type: str
    success: bool
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'instruction': self.instruction,
            'result': self.result,
            'timestamp': self.timestamp.isoformat(),
            'task_type': self.task_type,
            'success': self.success,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            instruction=data['instruction'],
            result=data['result'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            task_type=data['task_type'],
            success=data['success'],
            metadata=data.get('metadata', {})
        )


@dataclass
class SessionContext:
    """Session context information"""
    session_id: str
    start_time: datetime
    last_activity: datetime
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    current_task: Optional[str] = None
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'total_tasks': self.total_tasks,
            'successful_tasks': self.successful_tasks,
            'failed_tasks': self.failed_tasks,
            'current_task': self.current_task,
            'preferences': self.preferences
        }


class SessionMemory:
    """Session memory manager for maintaining context and task history"""
    
    def __init__(self, persist_to_disk: bool = True, memory_file: str = "session_memory.json"):
        self.persist_to_disk = persist_to_disk
        self.memory_file = Path(memory_file)
        self.memories: List[MemoryEntry] = []
        self.session_context: Optional[SessionContext] = None
        self.max_memories = 100  # Maximum number of memories to keep
        self.memory_ttl_days = 7  # Memory time-to-live in days
        
        if self.persist_to_disk:
            self._load_from_disk()
        
        # Initialize session if not exists
        if not self.session_context:
            self._initialize_session()
    
    def _initialize_session(self):
        """Initialize a new session"""
        self.session_context = SessionContext(
            session_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            last_activity=datetime.now(),
            total_tasks=0,
            successful_tasks=0,
            failed_tasks=0
        )
        logger.info(f"Initialized new session: {self.session_context.session_id}")
    
    def _load_from_disk(self):
        """Load memory from disk"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load memories
                self.memories = [
                    MemoryEntry.from_dict(mem_data)
                    for mem_data in data.get('memories', [])
                ]
                
                # Load session context
                if 'session_context' in data:
                    ctx_data = data['session_context']
                    self.session_context = SessionContext(
                        session_id=ctx_data['session_id'],
                        start_time=datetime.fromisoformat(ctx_data['start_time']),
                        last_activity=datetime.fromisoformat(ctx_data['last_activity']),
                        total_tasks=ctx_data['total_tasks'],
                        successful_tasks=ctx_data['successful_tasks'],
                        failed_tasks=ctx_data['failed_tasks'],
                        current_task=ctx_data.get('current_task'),
                        preferences=ctx_data.get('preferences', {})
                    )
                
                logger.info(f"Loaded {len(self.memories)} memories from disk")
                
        except Exception as e:
            logger.error(f"Failed to load memory from disk: {e}")
            self.memories = []
            self._initialize_session()
    
    def _save_to_disk(self):
        """Save memory to disk"""
        if not self.persist_to_disk:
            return
        
        try:
            data = {
                'memories': [mem.to_dict() for mem in self.memories],
                'session_context': self.session_context.to_dict() if self.session_context else None
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Saved memory to disk")
            
        except Exception as e:
            logger.error(f"Failed to save memory to disk: {e}")
    
    def add_memory(self, instruction: str, result: Dict[str, Any], success: bool = True, task_type: str = "unknown", metadata: Dict[str, Any] = None) -> str:
        """Add a new memory entry"""
        try:
            memory_id = str(uuid.uuid4())
            
            entry = MemoryEntry(
                id=memory_id,
                instruction=instruction,
                result=result,
                timestamp=datetime.now(),
                task_type=task_type,
                success=success,
                metadata=metadata or {}
            )
            
            self.memories.append(entry)
            
            # Update session context
            if self.session_context:
                self.session_context.total_tasks += 1
                if success:
                    self.session_context.successful_tasks += 1
                else:
                    self.session_context.failed_tasks += 1
                self.session_context.last_activity = datetime.now()
            
            # Cleanup old memories
            self._cleanup_old_memories()
            
            # Save to disk
            self._save_to_disk()
            
            logger.info(f"Added memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return ""
    
    def get_recent_memories(self, limit: int = 10) -> List[MemoryEntry]:
        """Get recent memory entries"""
        return sorted(self.memories, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_memories_by_type(self, task_type: str) -> List[MemoryEntry]:
        """Get memories by task type"""
        return [mem for mem in self.memories if mem.task_type == task_type]
    
    def get_successful_memories(self) -> List[MemoryEntry]:
        """Get successful memory entries"""
        return [mem for mem in self.memories if mem.success]
    
    def get_failed_memories(self) -> List[MemoryEntry]:
        """Get failed memory entries"""
        return [mem for mem in self.memories if not mem.success]
    
    def find_similar_memories(self, instruction: str, limit: int = 5) -> List[MemoryEntry]:
        """Find memories similar to the given instruction"""
        # Simple keyword-based similarity
        instruction_words = set(instruction.lower().split())
        
        scored_memories = []
        for mem in self.memories:
            memory_words = set(mem.instruction.lower().split())
            similarity = len(instruction_words.intersection(memory_words)) / len(instruction_words.union(memory_words))
            scored_memories.append((mem, similarity))
        
        # Sort by similarity and return top results
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return [mem for mem, score in scored_memories[:limit] if score > 0]
    
    def get_context_for_instruction(self, instruction: str) -> Dict[str, Any]:
        """Get relevant context for a new instruction"""
        context = {
            'similar_tasks': self.find_similar_memories(instruction, limit=3),
            'recent_tasks': self.get_recent_memories(limit=5),
            'session_stats': self.get_session_stats(),
            'preferences': self.get_preferences()
        }
        
        return context
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        if not self.session_context:
            return {}
        
        return {
            'session_id': self.session_context.session_id,
            'start_time': self.session_context.start_time.isoformat(),
            'last_activity': self.session_context.last_activity.isoformat(),
            'total_tasks': self.session_context.total_tasks,
            'successful_tasks': self.session_context.successful_tasks,
            'failed_tasks': self.session_context.failed_tasks,
            'success_rate': (
                self.session_context.successful_tasks / self.session_context.total_tasks
                if self.session_context.total_tasks > 0 else 0
            )
        }
    
    def get_preferences(self) -> Dict[str, Any]:
        """Get user preferences"""
        if not self.session_context:
            return {}
        
        return self.session_context.preferences
    
    def update_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences"""
        if self.session_context:
            self.session_context.preferences.update(preferences)
            self._save_to_disk()
    
    def _cleanup_old_memories(self):
        """Remove old memories to prevent memory bloat"""
        try:
            # Remove memories older than TTL
            cutoff_date = datetime.now() - timedelta(days=self.memory_ttl_days)
            self.memories = [mem for mem in self.memories if mem.timestamp > cutoff_date]
            
            # Limit total number of memories
            if len(self.memories) > self.max_memories:
                # Keep only the most recent memories
                self.memories = sorted(self.memories, key=lambda x: x.timestamp, reverse=True)[:self.max_memories]
            
            logger.debug(f"Cleaned up memories, now have {len(self.memories)} entries")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old memories: {e}")
    
    def clear_memories(self):
        """Clear all memories"""
        self.memories = []
        if self.session_context:
            self.session_context.total_tasks = 0
            self.session_context.successful_tasks = 0
            self.session_context.failed_tasks = 0
        self._save_to_disk()
        logger.info("Cleared all memories")
    
    def export_memories(self, filename: Optional[str] = None) -> str:
        """Export memories to a file"""
        try:
            if not filename:
                filename = f"memories_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'session_context': self.session_context.to_dict() if self.session_context else None,
                'memories': [mem.to_dict() for mem in self.memories],
                'total_memories': len(self.memories)
            }
            
            filepath = Path(filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(self.memories)} memories to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export memories: {e}")
            return ""
    
    def import_memories(self, filename: str) -> bool:
        """Import memories from a file"""
        try:
            filepath = Path(filename)
            if not filepath.exists():
                logger.error(f"Import file not found: {filename}")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_count = 0
            for mem_data in data.get('memories', []):
                try:
                    entry = MemoryEntry.from_dict(mem_data)
                    self.memories.append(entry)
                    imported_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import memory entry: {e}")
                    continue
            
            self._save_to_disk()
            logger.info(f"Imported {imported_count} memories from {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import memories: {e}")
            return False


class MemoryFactory:
    """Factory for creating memory instances"""
    
    @staticmethod
    def create_memory(persist_to_disk: bool = True, memory_file: str = "session_memory.json") -> SessionMemory:
        """Create a session memory instance"""
        return SessionMemory(persist_to_disk, memory_file)


# Example usage
if __name__ == "__main__":
    # Test the memory system
    memory = MemoryFactory.create_memory()
    
    # Add some test memories
    memory.add_memory(
        instruction="search laptops under 50000",
        result={"count": 5, "items": ["laptop1", "laptop2"]},
        success=True,
        task_type="search"
    )
    
    memory.add_memory(
        instruction="navigate to example.com",
        result={"url": "https://example.com", "status": "success"},
        success=True,
        task_type="navigate"
    )
    
    # Get recent memories
    recent = memory.get_recent_memories(5)
    print(f"Recent memories: {len(recent)}")
    
    # Get session stats
    stats = memory.get_session_stats()
    print(f"Session stats: {stats}")
    
    # Find similar memories
    similar = memory.find_similar_memories("search for laptops", limit=3)
    print(f"Similar memories: {len(similar)}")
