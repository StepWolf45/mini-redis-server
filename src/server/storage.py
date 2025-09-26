"""
Система хранения данных c поддержкой TTL.
"""
import asyncio
import heapq
import time
from typing import Any, Dict, Optional, Tuple
import fnmatch
from dataclasses import dataclass
import threading


@dataclass
class StorageItem:
    """Элемент хранения c TTL."""
    value: Any
    expire_at: Optional[float] = None 
    
    def is_expired(self) -> bool:
        """Проверяет, истек ли срок действия элемента."""
        if self.expire_at is None:
            return False
        return time.time() > self.expire_at


class Storage:
    """
    Основное хранилище данных c поддержкой TTL.
    Потокобезопасное хранилище в памяти.
    """
    
    def __init__(self):
        self._data: Dict[str, StorageItem] = {}
        self._lock = threading.RLock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 1.0 #сек
        self._expire_heap = []  
    
    async def start_cleanup_task(self):
        """Запускает фоновую задачу очистки истекших элементов."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())
    
    async def stop_cleanup_task(self):
        """Останавливает фоновую задачу очистки."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_expired(self):
        """Фоновая задача для удаления истекших элементов."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired_items()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Ошибка в cleanup task: {e}")
    
    async def _cleanup_expired_items(self):
        """Удаляет истекшие элементы используя heap."""
        with self._lock:
            current_time = time.time()
            while self._expire_heap and self._expire_heap[0][0] <= current_time:
                expire_at, key = heapq.heappop(self._expire_heap)
                if key in self._data and self._data[key].expire_at == expire_at:
                    del self._data[key]
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """
        Устанавливает значение для ключа.

        Args:
            key: Ключ
            value: Значение
            ttl: Время жизни в секундах (None для бессрочного хранения)

        Returns:
            True если операция успешна
        """
        with self._lock:
            expire_at = None
            if ttl is not None and ttl > 0:
                expire_at = time.time() + ttl
                heapq.heappush(self._expire_heap, (expire_at, key))

            self._data[key] = StorageItem(value=value, expire_at=expire_at)
            return True
    
    def get(self, key: str) -> Tuple[bool, Optional[Any]]:
        """
        Получает значение по ключу.
        
        Args:
            key: Ключ
            
        Returns:
            Tuple[bool, Optional[Any]]: (найден, значение)
        """
        with self._lock:
            if key not in self._data:
                return False, None
            
            item = self._data[key]
            if item.is_expired():
                del self._data[key]
                return False, None
            
            return True, item.value
    
    def delete(self, key: str) -> bool:
        """
        Удаляет ключ.
        
        Args:
            key: Ключ
            
        Returns:
            True если ключ был удален, False если не существовал
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """
        Проверяет существование ключа.
        
        Args:
            key: Ключ
            
        Returns:
            True если ключ существует и не истек
        """
        with self._lock:
            if key not in self._data:
                return False
            
            item = self._data[key]
            if item.is_expired():
                del self._data[key]
                return False
            
            return True
    
    def ttl(self, key: str) -> int:
        """
        Возвращает TTL ключа в секундах.
        
        Args:
            key: Ключ
            
        Returns:
            TTL в секундах, -1 если бессрочный, -2 если не существует
        """
        with self._lock:
            if key not in self._data:
                return -2
            
            item = self._data[key]
            if item.is_expired():
                del self._data[key]
                return -2
            
            if item.expire_at is None:
                return -1
            
            remaining = int(item.expire_at - time.time())
            return max(0, remaining)
    
    def expire(self, key: str, ttl: float) -> bool:
        """
        Устанавливает TTL для существующего ключа.

        Args:
            key: Ключ
            ttl: Время жизни в секундах

        Returns:
            True если TTL установлен, False если ключ не существует
        """
        with self._lock:
            if key not in self._data:
                return False

            item = self._data[key]
            if item.is_expired():
                del self._data[key]
                return False

            item.expire_at = time.time() + ttl
            heapq.heappush(self._expire_heap, (item.expire_at, key))
            return True
    
    def keys(self, pattern: str = "*") -> list:
        """
        Возвращает список ключей, соответствующих паттерну.
        
        Args:
            pattern: Паттерн для поиска (пока поддерживается только "*")
            
        Returns:
            Список ключей
        """
        with self._lock:
            expired_keys = [
                key for key, item in self._data.items() 
                if item.is_expired()
            ]
            for key in expired_keys:
                del self._data[key]
            
            if pattern == "*":
                return list(self._data.keys())
            
            result = []
            for key in self._data.keys():
                if self._match_pattern(key, pattern):
                    result.append(key)
            return result
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Сопоставление паттернов по правилам glob (*, ?, [seq])."""
        return fnmatch.fnmatchcase(key, pattern)
    
    def size(self) -> int:
        """Возвращает количество активных ключей."""
        with self._lock:
            expired_keys = [
                key for key, item in self._data.items() 
                if item.is_expired()
            ]
            for key in expired_keys:
                del self._data[key]
            
            return len(self._data)
    
    def clear(self):
        """Очищает все данные."""
        with self._lock:
            self._data.clear()
            self._expire_heap.clear()
