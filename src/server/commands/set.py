from typing import List, Any, Tuple
from .base_abstraction import Command, register_command


@register_command("SET")
class SetCommand(Command):
    """Команда SET для установки значения по ключу."""
    
    def __init__(self, storage):
        self.storage = storage
    
    def execute(self, args: List[str]) -> Tuple[bool, Any]:
        """
        Выполняет команду SET.
        
        Синтаксис: SET key value [EX seconds] [PX milliseconds]
        
        Args:
            args: [key, value, ...options]
            
        Returns:
            Tuple[bool, Any]: (успех, результат)
        """
        if not self.validate_args(args, 2):
            return False, "ERR: wrong number of arguments for 'set' command"
        
        key = args[0]
        value = args[1]
        

        ttl = None
        i = 2
        while i < len(args):
            if args[i].upper() == "EX" and i + 1 < len(args):
                # EX - время в секундах
                try:
                    ttl = float(args[i + 1])
                    if ttl <= 0:
                        return False, "ERR: invalid expire time in 'set' command"
                except ValueError:
                    return False, "ERR: value is not an integer or out of range"
                i += 2
            elif args[i].upper() == "PX" and i + 1 < len(args):
                # PX - время в миллисекундах
                try:
                    ttl = float(args[i + 1]) / 1000.0  # Конвертируем в секунды
                    if ttl <= 0:
                        return False, "ERR: invalid expire time in 'set' command"
                except ValueError:
                    return False, "ERR: value is not an integer or out of range"
                i += 2
            else:
                return False, f"ERR: syntax error in 'set' command: unknown option '{args[i]}'"

        success = self.storage.set(key, value, ttl)
        if success:
            return True, "OK"
        else:
            return False, "ERR: failed to set value"
    
    def get_name(self) -> str:
        """Возвращает имя команды."""
        return "SET"
