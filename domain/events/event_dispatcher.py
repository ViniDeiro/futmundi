"""
Implementação do despachante de eventos de domínio.
Responsável por registrar ouvintes (listeners) e disparar eventos para os mesmos.
"""
from typing import Dict, List, Type, Callable, Any
import logging

from domain.events.event import DomainEvent

# Configuração de logging
logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Despachante de eventos que gerencia a relação entre eventos e ouvintes.
    Implementa o padrão Publisher-Subscriber para eventos de domínio.
    """
    _instance = None
    _listeners: Dict[str, List[Callable[[DomainEvent], Any]]] = {}
    
    def __new__(cls):
        """
        Implementação do padrão Singleton.
        """
        if cls._instance is None:
            cls._instance = super(EventDispatcher, cls).__new__(cls)
            cls._instance._listeners = {}
        return cls._instance
    
    def register_listener(self, event_type: str, listener: Callable[[DomainEvent], Any]) -> None:
        """
        Registra um ouvinte para um tipo específico de evento.
        
        Args:
            event_type: O tipo de evento (normalmente o nome da classe do evento)
            listener: A função ou método que será chamado quando o evento for disparado
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        
        if listener not in self._listeners[event_type]:
            logger.debug(f"Registrando listener para evento {event_type}")
            self._listeners[event_type].append(listener)
    
    def register_listener_for_all(self, listener: Callable[[DomainEvent], Any]) -> None:
        """
        Registra um ouvinte para todos os tipos de eventos.
        
        Args:
            listener: A função ou método que será chamado quando qualquer evento for disparado
        """
        self.register_listener("*", listener)
    
    def unregister_listener(self, event_type: str, listener: Callable[[DomainEvent], Any]) -> None:
        """
        Remove um ouvinte registrado para um tipo específico de evento.
        
        Args:
            event_type: O tipo de evento
            listener: O ouvinte a ser removido
        """
        if event_type in self._listeners and listener in self._listeners[event_type]:
            self._listeners[event_type].remove(listener)
            logger.debug(f"Removendo listener para evento {event_type}")
    
    def dispatch(self, event: DomainEvent) -> None:
        """
        Dispara um evento para todos os ouvintes registrados.
        
        Args:
            event: O evento a ser disparado
        """
        event_type = event.event_type
        logger.debug(f"Disparando evento {event_type} - ID: {event.event_id}")
        
        # Notifica os ouvintes específicos do evento
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                try:
                    listener(event)
                except Exception as e:
                    logger.error(f"Erro ao processar evento {event_type} - ID: {event.event_id}: {str(e)}")
        
        # Notifica os ouvintes gerais (registrados para todos os eventos)
        if "*" in self._listeners:
            for listener in self._listeners["*"]:
                try:
                    listener(event)
                except Exception as e:
                    logger.error(f"Erro ao processar evento {event_type} (listener global) - ID: {event.event_id}: {str(e)}")


# Instância global do dispatcher
dispatcher = EventDispatcher() 