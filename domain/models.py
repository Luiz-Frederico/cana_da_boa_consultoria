from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class Insumo:
    produto: str
    litros_necessarios: float
    taxa_aplicacao_ml_por_m2: float

    def __str__(self) -> str:
        return f"Produto: {self.produto} - Necessário: {self.litros_necessarios:.2f} L @ {self.taxa_aplicacao_ml_por_m2} mL/m²"

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


@dataclass
class Planta:
    espacamento_ruas: float

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


@dataclass
class DetalhesPlantio:
    metodo: str
    detalhe_principal: str
    classificacao: str
    feedback: str

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__


class Cultura(ABC):
    """Classe Abstrata Base para representar uma cultura."""
    def __init__(self, nome: str, planta: Planta, detalhes_plantio: DetalhesPlantio):
        self.nome = nome
        self.planta = planta
        self.detalhes_plantio = detalhes_plantio
        self.insumo: Optional[Insumo] = None

    @abstractmethod
    def calcular_area_total(self) -> float:
        pass

    @abstractmethod
    def calcular_area_plantada(self) -> float:
        pass

    @abstractmethod
    def calcular_num_ruas(self) -> int:
        pass

    @abstractmethod
    def obter_detalhes(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass


class Cana(Cultura):
    """Representa uma plantação de Cana-de-Açúcar em um terreno Retangular/Talhão."""
    def __init__(self, propriedade: str, talhao: str, comprimento: float, largura: float, planta: Planta,
                 classificacao_dimensoes: str, classificacao_topografica: str, classificacao_espacamento_ruas: str,
                 detalhes_plantio: DetalhesPlantio, epoca_plantio: str, classificacao_epoca: str, feedback_epoca: str,
                 tipo_terreno_original: str,
                 possui_irrigacao: bool, preparo_solo_seco: bool,
                 controle_pragas: bool, planejamento_colheita_escalonado: bool,
                 controle_trajeto_maquinario: bool, mao_de_obra_especializada: bool,
                 variedades_adequadas_mecanizacao: bool, uso_piloto_automatico: bool,
                 velocidade_colhedora_acima_recomendada: bool,
                 id: Optional[int] = None, data: Optional[str] = None):  

        super().__init__("cana", planta, detalhes_plantio)
        self.id = id      
        self.data = data  
        self.propriedade = propriedade
        self.talhao = talhao
        self.comprimento = comprimento
        self.largura = largura
        self.classificacao_dimensoes = classificacao_dimensoes
        self.classificacao_topografica = classificacao_topografica
        self.classificacao_espacamento_ruas = classificacao_espacamento_ruas
        self.tipo_terreno_original = tipo_terreno_original
        self.possui_irrigacao = possui_irrigacao
        self.preparo_solo_seco = preparo_solo_seco
        self.controle_pragas = controle_pragas
        self.planejamento_colheita_escalonado = planejamento_colheita_escalonado
        self.controle_trajeto_maquinario = controle_trajeto_maquinario
        self.mao_de_obra_especializada = mao_de_obra_especializada
        self.variedades_adequadas_mecanizacao = variedades_adequadas_mecanizacao
        self.uso_piloto_automatico = uso_piloto_automatico
        self.velocidade_colhedora_acima_recomendada = velocidade_colhedora_acima_recomendada
        self.epoca_plantio = epoca_plantio
        self.classificacao_epoca = classificacao_epoca
        self.feedback_epoca = feedback_epoca
        
        self.pontuacao_risco: Optional[int] = None
        self.classificacao_risco: Optional[str] = None
        self.probabilidade_sucesso: Optional[str] = None
        self.pontos_atencao: Optional[List[str]] = None
        self.veto_agronomico: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        
        resultado = {
            "id": self.id,      
            "nome": self.nome,
            "propriedade": self.propriedade,
            "data": self.data,  
            "talhao": self.talhao,
            "comprimento": self.comprimento,
            "largura": self.largura,
            "classificacao_dimensoes": self.classificacao_dimensoes,
            "classificacao_topografica": self.classificacao_topografica,
            "classificacao_espacamento_ruas": self.classificacao_espacamento_ruas,
            "epoca_plantio": self.epoca_plantio,
            "classificacao_epoca": self.classificacao_epoca,
            "feedback_epoca": self.feedback_epoca,
            "tipo_terreno_original": self.tipo_terreno_original,
            "possui_irrigacao": self.possui_irrigacao,
            "preparo_solo_seco": self.preparo_solo_seco,
            "controle_pragas": self.controle_pragas,
            "planejamento_colheita_escalonado": self.planejamento_colheita_escalonado,
            "controle_trajeto_maquinario": self.controle_trajeto_maquinario,
            "mao_de_obra_especializada": self.mao_de_obra_especializada,
            "variedades_adequadas_mecanizacao": self.variedades_adequadas_mecanizacao,
            "uso_piloto_automatico": self.uso_piloto_automatico,
            "velocidade_colhedora_acima_recomendada": self.velocidade_colhedora_acima_recomendada,
            "planta": self.planta.to_dict(),
            "detalhes_plantio": self.detalhes_plantio.to_dict(),
            "insumo": self.insumo.to_dict() if self.insumo else None,
            "pontuacao_risco": self.pontuacao_risco,
            "classificacao_risco": self.classificacao_risco,
            "probabilidade_sucesso": self.probabilidade_sucesso,
            "veto_agronomico": self.veto_agronomico
        }
        return resultado

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Cana':
        planta = Planta(**data['planta'])
        detalhes_plantio = DetalhesPlantio(**data['detalhes_plantio'])
        cana = Cana(
            id=data.get('id'),      
            data=data.get('data'),  
            propriedade=data['propriedade'],
            talhao=data['talhao'],
            comprimento=data['comprimento'],
            largura=data['largura'],
            planta=planta,
            classificacao_dimensoes=data['classificacao_dimensoes'],
            classificacao_topografica=data['classificacao_topografica'],
            classificacao_espacamento_ruas=data['classificacao_espacamento_ruas'],
            detalhes_plantio=detalhes_plantio,
            epoca_plantio=data['epoca_plantio'],
            classificacao_epoca=data['classificacao_epoca'],
            feedback_epoca=data['feedback_epoca'],
            tipo_terreno_original=data.get('tipo_terreno_original', 'desconhecido'),
            possui_irrigacao=data.get('possui_irrigacao', False),
            preparo_solo_seco=data.get('preparo_solo_seco', False),
            controle_pragas=data.get('controle_pragas', False),
            planejamento_colheita_escalonado=data.get('planejamento_colheita_escalonado', False),
            controle_trajeto_maquinario=data.get('controle_trajeto_maquinario', False),
            mao_de_obra_especializada=data.get('mao_de_obra_especializada', False),
            variedades_adequadas_mecanizacao=data.get('variedades_adequadas_mecanizacao', False),
            uso_piloto_automatico=data.get('uso_piloto_automatico', False),
            velocidade_colhedora_acima_recomendada=data.get('velocidade_colhedora_acima_recomendada', False)
        )
        if data['insumo']:
            cana.insumo = Insumo(**data['insumo'])
            
        cana.pontuacao_risco = data.get('pontuacao_risco')
        cana.classificacao_risco = data.get('classificacao_risco')
        cana.probabilidade_sucesso = data.get('probabilidade_sucesso')
        cana.veto_agronomico = data.get('veto_agronomico')
        return cana

    def calcular_area_total(self) -> float:
        return self.comprimento * self.largura

    def calcular_num_ruas(self) -> int:
        return int(self.largura / self.planta.espacamento_ruas)

    def calcular_area_plantada(self) -> float:
        num_linhas = self.calcular_num_ruas()
        area_por_linha = self.comprimento * self.planta.espacamento_ruas
        return area_por_linha * num_linhas

    def obter_detalhes(self) -> Dict[str, Any]:
        return {
            "Tipo de Terreno": "Retangular/Talhão",
            "Classificação Topográfica": self.classificacao_topografica,
            "Classificação Espacamento Ruas": self.classificacao_espacamento_ruas,
            "Classificação Dimensões": self.classificacao_dimensoes,
            "Comprimento": f"{self.comprimento:.2f} m",
            "Largura": f"{self.largura:.2f} m",
            "Espaçamento Ruas": f"{self.planta.espacamento_ruas:.2f} m",
            "Método Plantio": self.detalhes_plantio.metodo,
            "Detalhe Plantio": self.detalhes_plantio.detalhe_principal,
            "Classificação Plantio": self.detalhes_plantio.classificacao,
            "Época de Plantio": self.epoca_plantio.capitalize(),
            "Classificação Época": self.classificacao_epoca,
            "Dado Original Terreno": self.tipo_terreno_original.capitalize(),
            "Possui Irrigação": "Sim" if self.possui_irrigacao else "Não",
            "Preparo Solo Seca": "Sim" if self.preparo_solo_seco else "Não",
            "Controle Pragas/Doenças": "Sim" if self.controle_pragas else "Não",
            "Planejamento Colheita Escalonado": "Sim" if self.planejamento_colheita_escalonado else "Não",
            "Controle Trajeto Maquinario": "Sim" if self.controle_trajeto_maquinario else "Não",
            "Mao de Obra Especializada": "Sim" if self.mao_de_obra_especializada else "Não",
            "Variedades Adequadas Mecanizacao": "Sim" if self.variedades_adequadas_mecanizacao else "Não",
            "Uso Piloto Automatico/GPS": "Sim" if self.uso_piloto_automatico else "Não",
            "Velocidade Colhedora Acima Recomendada": "Sim" if self.velocidade_colhedora_acima_recomendada else "Não"
        }

    def __str__(self) -> str:
        detalhes_dict = self.obter_detalhes()
        classificacao_dimensoes = detalhes_dict.pop("Classificação Dimensões", "N/A")
        classificacao_topografica = detalhes_dict.pop("Classificação Topográfica", "N/A")
        classificacao_espacamento_ruas = detalhes_dict.pop("Classificação Espacamento Ruas", "N/A")
        classificacao_plantio = detalhes_dict.pop("Classificação Plantio", "N/A")
        classificacao_epoca = detalhes_dict.pop("Classificação Época", "N/A")

        detalhes_keys_to_remove = ["Dado Original Terreno", "Possui Irrigação", "Preparo Solo Seca",
                                   "Controle Pragas/Doenças", "Planejamento Colheita Escalonado",
                                   "Controle Trajeto Maquinario", "Mao de Obra Especializada",
                                   "Variedades Adequadas Mecanizacao", "Uso Piloto Automatico/GPS",
                                   "Velocidade Colhedora Acima Recomendada"]
        for key in detalhes_keys_to_remove:
            detalhes_dict.pop(key, "N/A")

        detalhes = ', '.join(f"{k}: {v}" for k, v in detalhes_dict.items())
        info_insumo = f"Insumo: {self.insumo}" if self.insumo else ""
        info_risco = ""
        if self.pontuacao_risco is not None:
             info_risco = f" | RISCO: {self.classificacao_risco} ({self.pontuacao_risco} pts, {self.probabilidade_sucesso})"

        return (
                f"Cultura: {self.nome.capitalize()} - Propriedade: {self.propriedade} - Talhão: {self.talhao} | "
                f"Topografia: {classificacao_topografica} | Esp. Ruas: {classificacao_espacamento_ruas} | Plantio: {classificacao_plantio} | Época: {classificacao_epoca} | Dimensões: {classificacao_dimensoes}"
                f"{info_risco} | "
                f"Área Total: {self.calcular_area_total():.2f} m² | "
                f"Área Plantada: {self.calcular_area_plantada():.2f} m² | "
                f"Número de Ruas: {self.calcular_num_ruas()} | "
                f"Detalhes: ({detalhes})"
                + (f" | {info_insumo}" if info_insumo else "")
        )