"""
Команды для работы с TTL.
"""
from typing import List, Any, Tuple
from .base_abstraction import Command, register_command


@register_command("TTL")
class TtlCommand(Command):
    """Команда TTL для получения времени жизни ключа."""
    
    def __init__(self, storage):
        self.storage = storage
    
    def execute(self, args: List[str]) -> Tuple[bool, Any]:
        """
        Выполняет команду TTL.
        
        Синтаксис: TTL key
        
        Args:
            args: [key]
            
        Returns:
            Tuple[bool, Any]: (успех, TTL в секундах)
        """
        if not self.validate_args(args, 1, 1):
            return False, "ERR: wrong number of arguments for 'ttl' command"
        
        key = args[0]
        ttl = self.storage.ttl(key)
        
        return True, ttl
    
    def get_name(self) -> str:
        """Возвращает имя команды."""
        return "TTL"


@register_command("EXPIRE")
class ExpireCommand(Command):
    """Команда EXPIRE для установки времени жизни ключа."""
    
    def __init__(self, storage):
        self.storage = storage
    
    def execute(self, args: List[str]) -> Tuple[bool, Any]:
        """
        Выполняет команду EXPIRE.
        
        Синтаксис: EXPIRE key seconds
        
        Args:
            args: [key, seconds]
            
        Returns:
            Tuple[bool, Any]: (успех, результат)
        """
        if not self.validate_args(args, 2, 2):
            return False, "ERR: wrong number of arguments for 'expire' command"
        
        key = args[0]
        
        try:
            seconds = float(args[1])
            if seconds <= 0:
                return False, "ERR: invalid expire time in 'expire' command"
        except ValueError:
            return False, "ERR: value is not an integer or out of range"
        
        success = self.storage.expire(key, seconds)
        return True, 1 if success else 0
    
    def get_name(self) -> str:
        """Возвращает имя команды."""
        return "EXPIRE"


@register_command("EXISTS")
class ExistsCommand(Command):
    """Команда EXISTS для проверки существования ключа."""
    
    def __init__(self, storage):
        self.storage = storage
    
    def execute(self, args: List[str]) -> Tuple[bool, Any]:
        """
        Выполняет команду EXISTS.
        
        Синтаксис: EXISTS key [key ...]
        
        Args:
            args: [key1, key2, ...]
            
        Returns:
            Tuple[bool, Any]: (успех, количество существующих ключей)
        """
        if not self.validate_args(args, 1):
            return False, "ERR: wrong number of arguments for 'exists' command"
        
        count = 0
        for key in args:
            if self.storage.exists(key):
                count += 1
        
        return True, count
    
    def get_name(self) -> str:
        """Возвращает имя команды."""
        return "EXISTS"


@register_command("DEL")
class DelCommand(Command):
    """Команда DEL для удаления ключей."""
    
    def __init__(self, storage):
        self.storage = storage
    
    def execute(self, args: List[str]) -> Tuple[bool, Any]:
        """
        Выполняет команду DEL.
        
        Синтаксис: DEL key [key ...]
        
        Args:
            args: [key1, key2, ...]
            
        Returns:
            Tuple[bool, Any]: (успех, количество удаленных ключей)
        """
        if not self.validate_args(args, 1):
            return False, "ERR: wrong number of arguments for 'del' command"
        
        count = 0
        for key in args:
            if self.storage.delete(key):
                count += 1
        
        return True, count
    
    def get_name(self) -> str:
        """Возвращает имя команды."""
        return "DEL"


@register_command("KEYS")
class KeysCommand(Command):
    """Команда KEYS для получения списка ключей."""
    
    def __init__(self, storage):
        self.storage = storage
    
    def execute(self, args: List[str]) -> Tuple[bool, Any]:
        """
        Выполняет команду KEYS.
        
        Синтаксис: KEYS pattern
        
        Args:
            args: [pattern]
            
        Returns:
            Tuple[bool, Any]: (успех, список ключей)
        """
        if not self.validate_args(args, 1, 1):
            return False, "ERR: wrong number of arguments for 'keys' command"
        
        pattern = args[0]
        keys = self.storage.keys(pattern)
        
        return True, keys
    
    def get_name(self) -> str:
        """Возвращает имя команды."""
        return "KEYS"
