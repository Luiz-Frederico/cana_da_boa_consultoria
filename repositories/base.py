from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from domain.models import Cana


class PlantacaoRepository(ABC):
    """
    Interface abstrata que define o contrato para todos os repositórios
    de plantações (JSON, Oracle, etc.).
    
    Qualquer repositório concreto deve implementar todos os métodos abaixo.
    """
    
    @abstractmethod
    def adicionar(self, cultura: Cana) -> bool:
        """
        Adiciona uma nova plantação ao repositório.
        Retorna True se bem-sucedido, False caso contrário.
        """
        pass
    
    @abstractmethod
    def atualizar(self, cultura: Cana) -> bool:
        """
        Atualiza uma plantação existente no repositório.
        Retorna True se bem-sucedido, False caso contrário.
        """
        pass
    
    @abstractmethod
    def deletar(self, id_registro: int) -> bool:
        """
        Remove uma plantação do repositório pelo ID.
        Retorna True se removido, False se não encontrado.
        """
        pass
    
    @abstractmethod
    def obter_todos(self) -> List[Cana]:
        """
        Retorna uma lista com todas as plantações armazenadas.
        """
        pass
    
    @abstractmethod
    def obter_por_id(self, id_registro: int) -> Optional[Cana]:
        """
        Retorna uma plantação específica pelo ID, ou None se não encontrada.
        """
        pass
    
    @abstractmethod
    def sincronizar_lote(self, lista_plantacoes: List[Cana]) -> bool:
        """
        Sincroniza um lote de plantações em uma única operação (batch).
        Útil para upload em massa para o Oracle ou importação em lote.
        Retorna True se bem-sucedido.
        """
        pass
    
    @abstractmethod
    def inicializar_estrutura(self) -> bool:
        """
        Inicializa a estrutura de armazenamento (cria tabela no Oracle,
        ou garante que o arquivo JSON existe, etc.).
        Retorna True se bem-sucedido.
        """
        pass