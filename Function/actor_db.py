#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局演员数据库模块
用于管理跨数据源演员ID映射和本地头像
"""

import os
import json
import sqlite3
from configparser import ConfigParser

# 数据库文件路径
DB_FILE = 'actor_database.db'

class ActorDatabase:
    """演员数据库管理类"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), DB_FILE)
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 演员基本信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                name_en TEXT,
                birthdate TEXT,
                height TEXT,
                cup TEXT,
                debut_year TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 演员ID映射表（不同数据源的ID）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actor_ids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id INTEGER,
                source TEXT NOT NULL,
                source_id TEXT NOT NULL,
                UNIQUE(source, source_id),
                FOREIGN KEY (actor_id) REFERENCES actors(id)
            )
        ''')
        
        # 演员头像路径表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actor_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id INTEGER,
                photo_path TEXT,
                source_url TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (actor_id) REFERENCES actors(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_actor_by_source_id(self, source, source_id):
        """根据数据源ID获取演员信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.id, a.name, a.name_en 
            FROM actors a
            JOIN actor_ids ai ON a.id = ai.actor_id
            WHERE ai.source = ? AND ai.source_id = ?
        ''', (source, str(source_id)))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'name_en': result[2]
            }
        return None
    
    def add_actor(self, name, source, source_id, **kwargs):
        """添加演员到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查是否已存在
        existing = self.get_actor_by_source_id(source, source_id)
        if existing:
            conn.close()
            return existing['id']
        
        # 插入演员基本信息
        cursor.execute('''
            INSERT INTO actors (name, name_en, birthdate, height, cup, debut_year)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            name,
            kwargs.get('name_en', ''),
            kwargs.get('birthdate', ''),
            kwargs.get('height', ''),
            kwargs.get('cup', ''),
            kwargs.get('debut_year', '')
        ))
        
        actor_id = cursor.lastrowid
        
        # 插入数据源ID映射
        cursor.execute('''
            INSERT INTO actor_ids (actor_id, source, source_id)
            VALUES (?, ?, ?)
        ''', (actor_id, source, str(source_id)))
        
        conn.commit()
        conn.close()
        
        return actor_id
    
    def add_id_mapping(self, actor_name, source, source_id):
        """为已有演员添加新的数据源ID映射"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 查找演员
        cursor.execute('SELECT id FROM actors WHERE name = ?', (actor_name,))
        result = cursor.fetchone()
        
        if result:
            actor_id = result[0]
            # 检查映射是否已存在
            cursor.execute('''
                SELECT id FROM actor_ids 
                WHERE actor_id = ? AND source = ? AND source_id = ?
            ''', (actor_id, source, str(source_id)))
            
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO actor_ids (actor_id, source, source_id)
                    VALUES (?, ?, ?)
                ''', (actor_id, source, str(source_id)))
                conn.commit()
        
        conn.close()
    
    def get_all_ids_for_actor(self, actor_name):
        """获取演员在所有数据源的ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ai.source, ai.source_id
            FROM actor_ids ai
            JOIN actors a ON ai.actor_id = a.id
            WHERE a.name = ?
        ''', (actor_name,))
        
        results = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in results}
    
    def update_photo_path(self, actor_name, photo_path, source_url=None):
        """更新演员头像路径"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM actors WHERE name = ?', (actor_name,))
        result = cursor.fetchone()
        
        if result:
            actor_id = result[0]
            cursor.execute('''
                INSERT OR REPLACE INTO actor_photos (actor_id, photo_path, source_url)
                VALUES (?, ?, ?)
            ''', (actor_id, photo_path, source_url))
            conn.commit()
        
        conn.close()
    
    def get_photo_path(self, actor_name):
        """获取演员头像路径"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ap.photo_path
            FROM actor_photos ap
            JOIN actors a ON ap.actor_id = a.id
            WHERE a.name = ?
            ORDER BY ap.updated_at DESC
            LIMIT 1
        ''', (actor_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None


# 全局数据库实例
_actor_db = None

def get_actor_db():
    """获取全局演员数据库实例"""
    global _actor_db
    if _actor_db is None:
        _actor_db = ActorDatabase()
    return _actor_db


def normalize_actor_id(source, source_id, actor_name):
    """
    标准化演员ID
    返回格式: {source}:{source_id}
    同时保存到全局数据库
    """
    db = get_actor_db()
    
    # 添加到数据库
    db.add_actor(actor_name, source, source_id)
    
    # 返回标准格式的ID
    return f"{source}:{source_id}"


def get_actor_global_id(source, source_id):
    """
    获取演员的全局唯一ID
    如果在数据库中找到，返回全局ID；否则返回None
    """
    db = get_actor_db()
    actor = db.get_actor_by_source_id(source, source_id)
    
    if actor:
        return f"avdc:{actor['id']}"
    return None


def merge_actor_data(actor_data_list):
    """
    合并来自不同数据源的演员数据
    优先使用有ID的数据源
    
    Args:
        actor_data_list: 列表，每个元素是 {'source': 'javbus', 'actor_id': {...}, 'actor_photo': {...}}
    
    Returns:
        合并后的 {'actor_id': {...}, 'actor_photo': {...}, 'actor_ids_all': {...}}
    """
    merged_ids = {}
    merged_photos = {}
    all_ids = {}
    
    # 按优先级处理数据源（javbus优先，因为它有ID）
    priority = ['javbus', 'javdb', 'avsox', 'xcity', 'mgstage', 'dmm', 'jav321']
    
    # 按优先级排序
    sorted_data = sorted(actor_data_list, 
                        key=lambda x: priority.index(x['source']) if x['source'] in priority else 999)
    
    for data in sorted_data:
        source = data['source']
        actor_id_map = data.get('actor_id', {})
        actor_photo_map = data.get('actor_photo', {})
        
        for actor_name in actor_photo_map.keys():
            # 如果还没有这个演员的头像，添加它
            if actor_name not in merged_photos:
                merged_photos[actor_name] = actor_photo_map[actor_name]
            
            # 如果有ID，添加到ID映射
            if actor_name in actor_id_map and actor_id_map[actor_name]:
                # 标准化ID（添加数据源前缀）
                normalized_id = f"{source}:{actor_id_map[actor_name]}"
                merged_ids[actor_name] = normalized_id
                
                # 保存到全局数据库
                normalize_actor_id(source, actor_id_map[actor_name], actor_name)
    
    return {
        'actor_id': merged_ids,
        'actor_photo': merged_photos,
        'actor_ids_all': all_ids
    }


if __name__ == '__main__':
    # 测试
    db = get_actor_db()
    
    # 添加测试数据
    actor_id = db.add_actor('春陽モカ', 'javbus', '1248', name_en='Shunyo Moka')
    print(f"Added actor with ID: {actor_id}")
    
    # 添加另一个数据源的ID映射
    db.add_id_mapping('春陽モカ', 'javdb', 'abc123')
    
    # 获取所有ID
    all_ids = db.get_all_ids_for_actor('春陽モカ')
    print(f"All IDs: {all_ids}")
