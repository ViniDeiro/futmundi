"""
Classe base para eventos de domínio.
"""
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


@dataclass
class DomainEvent(ABC):
    """
    Classe base abstrata para todos os eventos de domínio.
    
    Cada evento representa um fato importante que ocorreu no domínio e
    pode ser utilizado para notificar outras partes do sistema sobre mudanças.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """
        Garante que os campos obrigatórios estejam preenchidos.
        """
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
            
        if not self.timestamp:
            self.timestamp = datetime.now()
            
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def event_type(self) -> str:
        """
        Retorna o tipo do evento, que é o nome da classe.
        
        Returns:
            O nome da classe do evento.
        """
        return self.__class__.__name__
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Adiciona um item de metadados ao evento.
        
        Args:
            key: A chave do metadado.
            value: O valor do metadado.
        """
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o evento para um dicionário.
        
        Returns:
            Um dicionário representando o evento.
        """
        # Obtem todos os campos do dataclass
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
        
        # Adiciona os campos específicos da subclasse
        for key, value in self.__dict__.items():
            if key not in ("event_id", "timestamp", "metadata"):
                result[key] = value
                
        return result 