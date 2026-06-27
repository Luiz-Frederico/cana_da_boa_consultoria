from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class RiscoResultado:
    """
    DTO que encapsula o resultado completo da avaliação de risco agronômico.
    Imutável (frozen=True) para garantir integridade dos dados.
    """
    pontuacao: int
    classificacao: str
    probabilidade_sucesso: str
    pontos_atencao: List[str]
    veto_agronomico: Optional[str]