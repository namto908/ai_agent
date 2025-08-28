"""
Memory Management System for AI Agent
Handles short-term and long-term memory storage
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

@dataclass
class MemoryEntry:
    """Represents a single memory entry"""
    id: str
    session_id: str
    user_id: str
    timestamp: str
    question: str
    answer: str
    intent: str
    tools_used: List[str]
    success: bool
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

@dataclass
class MemoryQuery:
    """Query parameters for memory retrieval"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    intent: Optional[str] = None
    tools_used: Optional[List[str]] = None
    time_range_days: Optional[int] = None
    limit: int = 10

class MemoryManager:
    """Manages both short-term and long-term memory for the AI agent"""
    
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self.short_term_memory: Dict[str, List[MemoryEntry]] = {}  # session_id -> entries
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database for long-term memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_entries (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                intent TEXT NOT NULL,
                tools_used TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                metadata TEXT NOT NULL,
                embedding TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON memory_entries(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON memory_entries(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_intent ON memory_entries(intent)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON memory_entries(timestamp)')
        
        conn.commit()
        conn.close()
    
    def add_memory(self, entry: MemoryEntry):
        """Add a memory entry to both short-term and long-term storage"""
        # Add to short-term memory
        if entry.session_id not in self.short_term_memory:
            self.short_term_memory[entry.session_id] = []
        self.short_term_memory[entry.session_id].append(entry)
        
        # Add to long-term memory (database)
        self._save_to_database(entry)
    
    def _save_to_database(self, entry: MemoryEntry):
        """Save memory entry to SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO memory_entries 
            (id, session_id, user_id, timestamp, question, answer, intent, tools_used, success, metadata, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.id,
            entry.session_id,
            entry.user_id,
            entry.timestamp,
            entry.question,
            entry.answer,
            entry.intent,
            json.dumps(entry.tools_used),
            entry.success,
            json.dumps(entry.metadata),
            json.dumps(entry.embedding) if entry.embedding else None
        ))
        
        conn.commit()
        conn.close()
    
    def get_short_term_memory(self, session_id: str, limit: int = 10) -> List[MemoryEntry]:
        """Get recent memory entries for a session"""
        if session_id not in self.short_term_memory:
            return []
        
        entries = self.short_term_memory[session_id]
        return entries[-limit:] if limit else entries
    
    def get_long_term_memory(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Get memory entries from long-term storage based on query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query conditions
        conditions = []
        params = []
        
        if query.user_id:
            conditions.append("user_id = ?")
            params.append(query.user_id)
        
        if query.session_id:
            conditions.append("session_id = ?")
            params.append(query.session_id)
        
        if query.intent:
            conditions.append("intent = ?")
            params.append(query.intent)
        
        if query.tools_used:
            # Search for entries that used any of the specified tools
            tool_conditions = []
            for tool in query.tools_used:
                tool_conditions.append("tools_used LIKE ?")
                params.append(f'%"{tool}"%')
            conditions.append(f"({' OR '.join(tool_conditions)})")
        
        if query.time_range_days:
            cutoff_date = (datetime.now() - timedelta(days=query.time_range_days)).isoformat()
            conditions.append("timestamp >= ?")
            params.append(cutoff_date)
        
        # Build the SQL query
        sql = "SELECT * FROM memory_entries"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(query.limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        # Convert rows to MemoryEntry objects
        entries = []
        for row in rows:
            entry = MemoryEntry(
                id=row[0],
                session_id=row[1],
                user_id=row[2],
                timestamp=row[3],
                question=row[4],
                answer=row[5],
                intent=row[6],
                tools_used=json.loads(row[7]),
                success=bool(row[8]),
                metadata=json.loads(row[9]),
                embedding=json.loads(row[10]) if row[10] else None
            )
            entries.append(entry)
        
        conn.close()
        return entries
    
    def search_similar_memories(self, question: str, user_id: str, limit: int = 5) -> List[MemoryEntry]:
        """Search for similar past questions using simple keyword matching"""
        # Simple keyword-based search (can be enhanced with embeddings later)
        keywords = question.lower().split()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search for questions containing any of the keywords
        conditions = []
        params = []
        
        for keyword in keywords:
            if len(keyword) > 2:  # Only search for meaningful keywords
                conditions.append("LOWER(question) LIKE ?")
                params.append(f'%{keyword}%')
        
        if not conditions:
            return []
        
        sql = f"""
            SELECT * FROM memory_entries 
            WHERE user_id = ? AND ({' OR '.join(conditions)})
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        params = [user_id] + params + [limit]
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        entries = []
        for row in rows:
            entry = MemoryEntry(
                id=row[0],
                session_id=row[1],
                user_id=row[2],
                timestamp=row[3],
                question=row[4],
                answer=row[5],
                intent=row[6],
                tools_used=json.loads(row[7]),
                success=bool(row[8]),
                metadata=json.loads(row[9]),
                embedding=json.loads(row[10]) if row[10] else None
            )
            entries.append(entry)
        
        conn.close()
        return entries
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's interaction history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total interactions
        cursor.execute("SELECT COUNT(*) FROM memory_entries WHERE user_id = ?", (user_id,))
        total_interactions = cursor.fetchone()[0]
        
        # Success rate
        cursor.execute("SELECT COUNT(*) FROM memory_entries WHERE user_id = ? AND success = 1", (user_id,))
        successful_interactions = cursor.fetchone()[0]
        success_rate = (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0
        
        # Most common intents
        cursor.execute("""
            SELECT intent, COUNT(*) as count 
            FROM memory_entries 
            WHERE user_id = ? 
            GROUP BY intent 
            ORDER BY count DESC 
            LIMIT 5
        """, (user_id,))
        common_intents = [{"intent": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Most used tools
        cursor.execute("""
            SELECT tools_used, COUNT(*) as count 
            FROM memory_entries 
            WHERE user_id = ? 
            GROUP BY tools_used 
            ORDER BY count DESC 
            LIMIT 5
        """, (user_id,))
        common_tools = []
        for row in cursor.fetchall():
            tools = json.loads(row[0])
            for tool in tools:
                found = False
                for item in common_tools:
                    if item["tool"] == tool:
                        item["count"] += row[1]
                        found = True
                        break
                if not found:
                    common_tools.append({"tool": tool, "count": row[1]})
        
        common_tools.sort(key=lambda x: x["count"], reverse=True)
        common_tools = common_tools[:5]
        
        # Recent activity
        cursor.execute("""
            SELECT DATE(timestamp) as date, COUNT(*) as count 
            FROM memory_entries 
            WHERE user_id = ? 
            GROUP BY DATE(timestamp) 
            ORDER BY date DESC 
            LIMIT 7
        """, (user_id,))
        recent_activity = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total_interactions": total_interactions,
            "success_rate": round(success_rate, 2),
            "common_intents": common_intents,
            "common_tools": common_tools,
            "recent_activity": recent_activity
        }
    
    def clear_session_memory(self, session_id: str):
        """Clear short-term memory for a specific session"""
        if session_id in self.short_term_memory:
            del self.short_term_memory[session_id]
    
    def clear_user_memory(self, user_id: str):
        """Clear all memory for a specific user"""
        # Clear short-term memory
        sessions_to_remove = []
        for session_id, entries in self.short_term_memory.items():
            if entries and entries[0].user_id == user_id:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.short_term_memory[session_id]
        
        # Clear long-term memory
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memory_entries WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
    
    def export_memory(self, user_id: str, format: str = "json") -> str:
        """Export user's memory to a file"""
        entries = self.get_long_term_memory(MemoryQuery(user_id=user_id, limit=1000))
        
        if format == "json":
            data = [asdict(entry) for entry in entries]
            filename = f"memory_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return filename
        
        return "Unsupported format"
    
    def get_memory_summary(self, user_id: str) -> str:
        """Generate a summary of user's memory"""
        stats = self.get_user_statistics(user_id)
        recent_memories = self.get_long_term_memory(
            MemoryQuery(user_id=user_id, limit=5)
        )
        
        summary = f"""
## 📊 Thống kê tương tác của bạn

**Tổng số lần tương tác:** {stats['total_interactions']}
**Tỷ lệ thành công:** {stats['success_rate']}%

### 🎯 Intent thường dùng:
"""
        for intent in stats['common_intents']:
            summary += f"- {intent['intent']}: {intent['count']} lần\n"
        
        summary += "\n### 🛠️ Tools thường dùng:\n"
        for tool in stats['common_tools']:
            summary += f"- {tool['tool']}: {tool['count']} lần\n"
        
        if recent_memories:
            summary += "\n### 📝 Câu hỏi gần đây:\n"
            for memory in recent_memories:
                summary += f"- {memory.question[:50]}...\n"
        
        return summary

# Global memory manager instance
_memory_manager = None

def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
