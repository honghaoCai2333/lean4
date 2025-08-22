#!/usr/bin/env python3

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class ProofDatabase:
    def __init__(self, db_path: str = "proof_history.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS proof_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                statement TEXT NOT NULL,
                proof_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def create_session(self, statement: str, title: str = None) -> int:
        """创建新的证明会话"""
        if not title:
            # 从命题中提取标题，限制长度
            title = statement[:50] + "..." if len(statement) > 50 else statement
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO proof_sessions (title, statement)
            VALUES (?, ?)
        ''', (title, statement))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def update_session_proof(self, session_id: int, proof_result: str):
        """更新会话的证明结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE proof_sessions 
            SET proof_result = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (proof_result, session_id))
        conn.commit()
        conn.close()
    
    def get_sessions(self, limit: int = None) -> List[Dict]:
        """获取历史会话列表"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
            SELECT id, title, statement, created_at, updated_at
            FROM proof_sessions 
            ORDER BY updated_at DESC
        '''
        
        if limit:
            query += f' LIMIT {limit}'
            
        cursor.execute(query)
        sessions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sessions
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        """获取特定会话详情"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM proof_sessions WHERE id = ?
        ''', (session_id,))
        session = cursor.fetchone()
        conn.close()
        return dict(session) if session else None
    
    def get_recent_sessions(self, limit: int = 3) -> List[Dict]:
        """获取最近的会话（用于前端侧边栏显示）"""
        return self.get_sessions(limit=limit)