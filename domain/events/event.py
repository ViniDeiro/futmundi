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
    # Usando init=False para evitar problemas com a ordem dos parâmetros
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)
    timestamp: datetime = field(default_factory=datetime.now, init=False)
    metadata: Dict[str, Any] = field(default_factory=dict, init=False)
    
    def __post_init__(self):
        """
        Inicializa os campos da classe base.
        """
        # Inicializa os campos com init=False
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.now()
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