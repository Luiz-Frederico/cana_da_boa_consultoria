import json
import os
import datetime
from typing import List, Optional, Dict, Any
from domain.models import Cana
from repositories.base import PlantacaoRepository
from config.settings import ARQUIVO_DADOS
from utils.sanitizer import remover_acentos, remover_parenteses


class JsonRepository(PlantacaoRepository):
    """
    Implementação do repositório usando arquivo JSON como armazenamento.
    Mantém a lista em memória e sincroniza com o arquivo em disco.
    """
    
    def __init__(self):
        self._plantacoes: List[Cana] = []
        self._proximo_id: int = 1
        self._carregar_arquivo()
    
    def _carregar_arquivo(self) -> None:
        """Carrega os dados do arquivo JSON para a memória."""
        if not os.path.exists(ARQUIVO_DADOS):
            self._plantacoes = []
            self._proximo_id = 1
            return
        
        try:
            with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
                dados_serializados = json.load(f)
            
            plantacoes_carregadas = []
            for data in dados_serializados:
                if data.get('nome') == 'cana':
                    # Garante campos obrigatórios para compatibilidade
                    if 'feedback_epoca' not in data:
                        data['feedback_epoca'] = ""
                    if 'detalhes_plantio' in data and 'feedback' not in data['detalhes_plantio']:
                        data['detalhes_plantio']['feedback'] = ""
                    plantacoes_carregadas.append(Cana.from_dict(data))
            
            self._plantacoes = plantacoes_carregadas
            
            # Atualiza o próximo ID baseado no maior ID existente
            ids_existentes = [c.id for c in self._plantacoes if c.id is not None]
            self._proximo_id = max(ids_existentes) + 1 if ids_existentes else 1
            
            print(f"\n> {len(self._plantacoes)} plantações carregadas de '{ARQUIVO_DADOS}'.")
            
        except (IOError, json.JSONDecodeError) as e:
            print(f"\n> ERRO ao carregar dados do JSON: {e}")
            self._plantacoes = []
            self._proximo_id = 1
        except Exception as e:
            print(f"\n> ERRO inesperado durante o carregamento: {e}")
            self._plantacoes = []
            self._proximo_id = 1
    
    def _salvar_arquivo(self) -> bool:
        """
        Salva os dados atuais em memória no arquivo JSON.
        Aplica as sanitizações e transformações necessárias (removendo
        campos como pontos_atencao e feedbacks internos).
        """
        dados_serializados = []
        for cultura in self._plantacoes:
            # Garante ID e Data para registros antigos
            if not getattr(cultura, 'data', None):
                cultura.data = datetime.date.today().strftime("%Y-%m-%d")
            if not getattr(cultura, 'id', None):
                cultura.id = self._proximo_id
                self._proximo_id += 1
            
            dados_cultura = cultura.to_dict()
            
            # --- HIGIENIZAÇÃO EXATAMENTE COMO NO GERENCIADOR ANTIGO ---
            # 1. Remove parênteses e acentos de todos os campos string
            for k, v in dados_cultura.items():
                if isinstance(v, str):
                    if "(" in v:
                        v = v.split("(")[0].strip()
                    v = remover_acentos(v)
                    dados_cultura[k] = v
            
            # 2. Sanitiza a classificação do detalhes_plantio (se existir)
            if dados_cultura.get('detalhes_plantio'):
                dp = dados_cultura['detalhes_plantio']
                if "(" in dp.get('classificacao', ''):
                    dp['classificacao'] = dp['classificacao'].split("(")[0].strip()
                dp['classificacao'] = remover_acentos(dp['classificacao'])
                # Remove o campo 'feedback' (não vai para o JSON)
                dp.pop('feedback', None)
            
            # 3. Remove o '%' da probabilidade_sucesso (salva apenas o número)
            if dados_cultura.get('probabilidade_sucesso'):
                dados_cultura['probabilidade_sucesso'] = dados_cultura['probabilidade_sucesso'].replace('%', '').strip()
            
            # 4. Remove pontos_atencao (não persistido no JSON)
            dados_cultura.pop('pontos_atencao', None)
            
            dados_serializados.append(dados_cultura)
        
        try:
            with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
                json.dump(dados_serializados, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"\n> ERRO ao salvar os dados: {e}")
            return False
    
    # --- Implementação dos métodos abstratos ---
    
    def adicionar(self, cultura: Cana) -> bool:
        """Adiciona uma nova plantação à lista e salva no JSON."""
        # Gera ID automático se não tiver
        if not getattr(cultura, 'id', None):
            cultura.id = self._proximo_id
            self._proximo_id += 1
        
        # Gera data se não tiver
        if not getattr(cultura, 'data', None):
            cultura.data = datetime.date.today().strftime("%Y-%m-%d")
        
        self._plantacoes.append(cultura)
        return self._salvar_arquivo()
    
    def atualizar(self, cultura: Cana) -> bool:
        """Atualiza uma plantação existente (pelo ID) e salva no JSON."""
        if cultura.id is None:
            return False
        
        for i, existente in enumerate(self._plantacoes):
            if existente.id == cultura.id:
                self._plantacoes[i] = cultura
                return self._salvar_arquivo()
        
        return False
    
    def deletar(self, id_registro: int) -> bool:
        """Remove uma plantação pelo ID e salva no JSON."""
        for i, cultura in enumerate(self._plantacoes):
            if cultura.id == id_registro:
                self._plantacoes.pop(i)
                return self._salvar_arquivo()
        return False
    
    def obter_todos(self) -> List[Cana]:
        """Retorna todas as plantações em memória."""
        return self._plantacoes.copy()
    
    def obter_por_id(self, id_registro: int) -> Optional[Cana]:
        """Retorna uma plantação específica pelo ID, ou None."""
        for cultura in self._plantacoes:
            if cultura.id == id_registro:
                return cultura
        return None
    
    def sincronizar_lote(self, lista_plantacoes: List[Cana]) -> bool:
        """
        Substitui toda a lista interna pela fornecida e salva.
        Útil para importar dados de outra fonte (ex: Oracle).
        """
        if not lista_plantacoes:
            return False
        
        # Atualiza IDs e datas para todos
        for cultura in lista_plantacoes:
            if not getattr(cultura, 'id', None):
                cultura.id = self._proximo_id
                self._proximo_id += 1
            if not getattr(cultura, 'data', None):
                cultura.data = datetime.date.today().strftime("%Y-%m-%d")
        
        self._plantacoes = lista_plantacoes
        return self._salvar_arquivo()
    
    def inicializar_estrutura(self) -> bool:
        """
        Garante que o arquivo JSON existe e está acessível.
        Se não existir, cria um arquivo vazio.
        """
        try:
            if not os.path.exists(ARQUIVO_DADOS):
                with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                print(f"\n> Arquivo '{ARQUIVO_DADOS}' criado com sucesso.")
            return True
        except IOError as e:
            print(f"\n> ERRO ao criar arquivo JSON: {e}")
            return False