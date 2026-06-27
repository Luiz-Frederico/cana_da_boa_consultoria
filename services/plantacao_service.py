from typing import List, Optional
from domain.models import Cana
from repositories.json_repository import JsonRepository
from repositories.oracle_repository import OracleRepository
from utils.sanitizer import normalizar_para_comparacao
from utils.helpers import _registrar_log


class PlantacaoService:
    """
    Camada de serviço que orquestra as operações entre os repositórios
    (JSON local e Oracle remoto). Substitui o antigo GerenciadorPlantacoes.
    """
    
    def __init__(self, json_repo: JsonRepository, oracle_repo: Optional[OracleRepository] = None):
        """
        Inicializa o serviço com os repositórios injetados.
        
        Args:
            json_repo: Repositório JSON (obrigatório)
            oracle_repo: Repositório Oracle (opcional, pode ser None se não conectado)
        """
        self.json_repo = json_repo
        self.oracle_repo = oracle_repo
        
        # Carrega automaticamente os dados do JSON (já feito pelo JsonRepository no __init__)
        _registrar_log("Serviço inicializado com sucesso.")
    
    # --- Operações CRUD ---
    
    def adicionar(self, cultura: Cana) -> bool:
        """
        Adiciona uma nova plantação.
        1. Persiste no JSON local.
        2. Se o Oracle estiver conectado, espelha em tempo real.
        """
        if self.json_repo.adicionar(cultura):
            # Espelhamento para Oracle (se conectado)
            if self.oracle_repo and self.oracle_repo.connection:
                self.oracle_repo.adicionar(cultura)
                _registrar_log(f"Plantação ID {cultura.id} espelhada no Oracle.")
            return True
        return False
    
    def atualizar(self, cultura: Cana) -> bool:
        """
        Atualiza uma plantação existente.
        1. Atualiza no JSON local.
        2. Se o Oracle estiver conectado, espelha em tempo real.
        """
        if self.json_repo.atualizar(cultura):
            if self.oracle_repo and self.oracle_repo.connection:
                self.oracle_repo.atualizar(cultura)
                _registrar_log(f"Plantação ID {cultura.id} atualizada no Oracle.")
            return True
        return False
    
    def remover_por_indice(self, indice: int) -> bool:
        """
        Remove uma plantação pelo índice da lista (1-based).
        1. Obtém a cultura pelo índice.
        2. Remove do JSON local.
        3. Se o Oracle estiver conectado, remove remotamente.
        """
        plantacoes = self.json_repo.obter_todos()
        if 0 <= indice - 1 < len(plantacoes):
            cultura = plantacoes[indice - 1]
            if self.json_repo.deletar(cultura.id):
                if self.oracle_repo and self.oracle_repo.connection:
                    self.oracle_repo.deletar(cultura.id)
                    _registrar_log(f"Plantação ID {cultura.id} removida do Oracle.")
                print(f"\n> Plantação no índice {indice} removida com sucesso!")
                _registrar_log(f"Plantação removida: ID {cultura.id} - {cultura.propriedade} - {cultura.talhao}")
                return True
        else:
            print("\n> Índice inválido.")
        return False
    
    def listar_todos(self) -> List[Cana]:
        """Retorna todas as plantações armazenadas localmente."""
        return self.json_repo.obter_todos()
    
    def obter_por_indice(self, indice: int) -> Optional[Cana]:
        """Obtém uma plantação específica pelo índice (1-based)."""
        plantacoes = self.json_repo.obter_todos()
        if 0 <= indice - 1 < len(plantacoes):
            return plantacoes[indice - 1]
        return None
    
    def obter_por_id(self, id_registro: int) -> Optional[Cana]:
        """Obtém uma plantação específica pelo ID."""
        return self.json_repo.obter_por_id(id_registro)
    
    # --- Validações ---
    
    def verificar_unicidade(self, propriedade: str, talhao: str, indice_atual: Optional[int] = None) -> Optional[str]:
        """
        Verifica se já existe uma plantação com a mesma propriedade e talhão.
        Ignora o índice atual (útil para atualizações).
        Retorna uma mensagem de erro ou None se estiver disponível.
        """
        propriedade_norm = normalizar_para_comparacao(propriedade)
        talhao_norm = normalizar_para_comparacao(talhao)
        plantacoes = self.json_repo.obter_todos()
        
        for i, cultura in enumerate(plantacoes):
            # Pula o próprio registro se estiver atualizando
            if indice_atual is not None and (indice_atual - 1) == i:
                continue
            
            prop_exist = normalizar_para_comparacao(cultura.propriedade)
            tal_exist = normalizar_para_comparacao(cultura.talhao)
            
            if propriedade_norm == prop_exist and talhao_norm == tal_exist:
                return "Talhão já cadastrado! Este talhão já está registrado para esta propriedade."
        return None
    
    # --- Persistência ---
    
    def salvar_json(self) -> bool:
        """Força a persistência dos dados no arquivo JSON (já é automático, mas mantido para compatibilidade)."""
        return self.json_repo._salvar_arquivo()
    
    # --- Sincronização com Oracle ---
    
    def sincronizar_todos(self) -> bool:
        """
        Sincroniza TODOS os dados locais (JSON) para o Oracle em lote (batch).
        Utiliza executemany para alta performance.
        """
        if not self.oracle_repo:
            print("\n> [Serviço] Repositório Oracle não configurado.")
            return False
        
        plantacoes = self.json_repo.obter_todos()
        if not plantacoes:
            print("\n> [Serviço] Nenhum dado local para sincronizar.")
            return False
        
        print(f"\n> [Serviço] Iniciando sincronização em lote de {len(plantacoes)} registros...")
        sucesso = self.oracle_repo.sincronizar_lote(plantacoes)
        
        if sucesso:
            print("> [Serviço] Sincronização em lote concluída com sucesso!")
            _registrar_log(f"Sincronização em lote finalizada. {len(plantacoes)} registros sincronizados.")
        else:
            print("> [Serviço] Falha na sincronização em lote.")
            _registrar_log("Falha na sincronização em lote.")
        
        return sucesso
    
    def inicializar_infraestrutura_oracle(self) -> bool:
        """
        Valida/cria a estrutura da tabela no Oracle.
        Deve ser chamado após a conexão ser estabelecida.
        """
        if not self.oracle_repo:
            print("\n> [Serviço] Repositório Oracle não configurado.")
            return False
        
        print("\n> [Serviço] Verificando integridade da tabela remota...")
        sucesso = self.oracle_repo.inicializar_estrutura()
        if sucesso:
            _registrar_log("Infraestrutura Oracle inicializada ou validada com sucesso.")
        else:
            _registrar_log("Falha na validação/inicialização da infraestrutura Oracle.")
        return sucesso
    
    # --- Gerenciamento de Conexão Oracle ---
    
    def conectar_oracle(self, user: str, password: str, dsn: str) -> bool:
        """
        Atualiza as credenciais do repositório Oracle e estabelece a conexão.
        """
        if not self.oracle_repo:
            print("\n> [Serviço] Repositório Oracle não disponível.")
            return False
        
        # Atualiza as credenciais no repositório
        self.oracle_repo.user = user
        self.oracle_repo.password = password
        self.oracle_repo.dsn = dsn
        
        # Tenta conectar
        conectado = self.oracle_repo._connect()
        if conectado:
            _registrar_log("Conexão Oracle estabelecida via serviço.")
        else:
            _registrar_log("Falha na conexão Oracle via serviço.")
        return conectado
    
    def desconectar_oracle(self):
        """Desconecta do Oracle de forma segura."""
        if self.oracle_repo:
            self.oracle_repo._disconnect()
            _registrar_log("Conexão Oracle encerrada via serviço.")
    
    def is_oracle_conectado(self) -> bool:
        """Retorna True se a conexão com o Oracle está ativa."""
        if not self.oracle_repo:
            return False
        return self.oracle_repo.connection is not None