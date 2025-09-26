from typing import List, Any, Tuple
from .base_abstraction import Command


class GetCommand(Command):
    """Команда GET для получения значения по ключу."""
    
    def __init__(self, storage):
        self.storage = storage
    
    def execute(self, args: List[str]) -> Tuple[bool, Any]:
        """
        Выполняет команду GET.
        
        Синтаксис: GET key
        
        Args:
            args: [key]
            
        Returns:
            Tuple[bool, Any]: (успех, значение или None)
        """
        if not self.validate_args(args, 1, 1):
            return False, "ERR: wrong number of arguments for 'get' command"
        
        key = args[0]
        found, value = self.storage.get(key)
        
        if found:
            return True, value
        else:
            return True, None 
    
    def get_name(self) -> str:
        """Возвращает имя команды."""
        return "GET"
