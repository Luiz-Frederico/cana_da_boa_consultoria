import oracledb
import json
import copy
from typing import List, Optional, Dict, Any
from domain.models import Cana
from repositories.base import PlantacaoRepository
from config.settings import ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN
from utils.sanitizer import remover_acentos, remover_parenteses, sanitizar_payload
from utils.helpers import _registrar_log


class OracleRepository(PlantacaoRepository):
    """
    Implementação do repositório usando Oracle Database.
    Utiliza MERGE (UPSERT) para inserção/atualização e executemany para batch.
    """
    
    def __init__(self):
        self.user = ORACLE_USER
        self.password = ORACLE_PASSWORD
        self.dsn = ORACLE_DSN
        self.connection = None
    
    def _connect(self) -> bool:
        """Estabelece conexão com o Oracle, com verificação de credenciais."""
        if self.user == 'SEU_USUARIO_AQUI' or self.dsn == 'SEU_DSN_AQUI':
            return False
        
        try:
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            if hasattr(self.connection, 'ping'):
                self.connection.ping()
            return True
        except oracledb.Error as e:
            _registrar_log(f"Erro ao conectar ao Oracle: {e}")
            print(f"\n> [Oracle] Erro de conexão: {e}")
            return False
    
    def _disconnect(self):
        """Fecha a conexão de forma resiliente."""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                _registrar_log(f"Aviso de desconexão: {e}")
            finally:
                self.connection = None
    
    def _ensure_connection(self) -> bool:
        """Garante que a conexão está ativa; tenta reconectar se necessário."""
        if self.connection is None:
            return self._connect()
        try:
            self.connection.ping()
            return True
        except Exception:
            self.connection = None
            return self._connect()
    
    def _preparar_payload(self, cultura: Cana) -> Dict[str, Any]:
        """
        Prepara o payload JSON para envio ao Oracle, aplicando a mesma
        sanitização do código original (remove acentos, parênteses e %).
        """
        # Converte para dicionário
        dados_dict = cultura.to_dict() if hasattr(cultura, 'to_dict') else cultura
        
        # Cria uma cópia profunda para não modificar o original
        payload = copy.deepcopy(dados_dict)
        
        # 1. Sanitização de strings (acentos e parênteses) em todo o payload
        payload = sanitizar_payload(payload, recursivo=True)
        
        # 2. Remove o % da probabilidade_sucesso (se for string)
        if "probabilidade_sucesso" in payload and isinstance(payload["probabilidade_sucesso"], str):
            payload["probabilidade_sucesso"] = payload["probabilidade_sucesso"].replace("%", "").strip()
        
        # 3. Garante que campos específicos fiquem com valores padrão (como no original)
        if "detalhes_plantio" in payload and isinstance(payload["detalhes_plantio"], dict):
            payload["detalhes_plantio"]["feedback"] = ""  # força vazio
        if "feedback_epoca" in payload:
            payload["feedback_epoca"] = "Sistema de Alto Risco Agronomico"
        
        # 4. Remove pontos_atencao (não vai para o banco)
        payload.pop("pontos_atencao", None)
        
        return payload
    
    def _executar_merge(self, cultura: Cana) -> bool:
        """
        Executa o MERGE (UPSERT) para uma única plantação, com reconexão automática
        em caso de falha de rede (DPY-4011).
        """
        if not self._ensure_connection():
            return False
        
        cursor = None
        try:
            payload = self._preparar_payload(cultura)
            json_str = json.dumps(payload, ensure_ascii=False)
            
            # Sanitiza os campos diretos
            risco_limpo = remover_parenteses(getattr(cultura, "classificacao_risco", "NAO AVALIADO"))
            risco_limpo = remover_acentos(risco_limpo)
            
            params = {
                "id": cultura.id,
                "prop": remover_acentos(cultura.propriedade),
                "dt": cultura.data,
                "talhao": remover_acentos(cultura.talhao),
                "risco": risco_limpo,
                "json_data": json_str
            }
            
            sql_merge = """
                MERGE INTO PLANTIO_CANA t
                USING (SELECT :id AS ID FROM DUAL) src
                ON (t.ID = src.ID)
                WHEN MATCHED THEN
                    UPDATE SET 
                        PROPRIEDADE      = :prop,
                        DATA_REGISTRO    = TO_DATE(:dt, 'YYYY-MM-DD'),
                        TALHAO           = :talhao,
                        RISCO_AGRONOMICO = :risco,
                        DADOS_JSON       = :json_data
                WHEN NOT MATCHED THEN
                    INSERT (ID, PROPRIEDADE, DATA_REGISTRO, TALHAO, RISCO_AGRONOMICO, DADOS_JSON)
                    VALUES (:id, :prop, TO_DATE(:dt, 'YYYY-MM-DD'), :talhao, :risco, :json_data)
            """
            
            cursor = self.connection.cursor()
            cursor.execute(sql_merge, params)
            self.connection.commit()
            return True
            
        except Exception as e:
            erro_str = str(e)
            # Tratamento de reconexão para erro DPY-4011 (perda de conexão)
            if "DPY-4011" in erro_str or "connection closed" in erro_str.lower():
                print("\n> [Oracle] Canal de comunicação interrompido. Reestabelecendo...")
                self.connection = None
                if self._connect():
                    try:
                        cursor = self.connection.cursor()
                        cursor.execute(sql_merge, params)
                        self.connection.commit()
                        return True
                    except Exception as e_retry:
                        _registrar_log(f"Falha na reconexão: {e_retry}")
            else:
                _registrar_log(f"Erro no MERGE: {e}")
                print(f"> [Oracle] Erro no MERGE: {e}")
            return False
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
    
    # --- Implementação dos métodos abstratos ---
    
    def adicionar(self, cultura: Cana) -> bool:
        """Insere uma nova plantação (ou atualiza se já existir)."""
        return self._executar_merge(cultura)
    
    def atualizar(self, cultura: Cana) -> bool:
        """Atualiza uma plantação existente (ou insere se não existir)."""
        return self._executar_merge(cultura)
    
    def deletar(self, id_registro: int) -> bool:
        """Remove uma plantação pelo ID."""
        if not self._ensure_connection():
            return False
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM PLANTIO_CANA WHERE ID = :id", {"id": id_registro})
            self.connection.commit()
            if cursor.rowcount > 0:
                print(f"> [Oracle] Registro ID {id_registro} removido com sucesso.")
                return True
            else:
                print(f"> [Oracle] Registro ID {id_registro} não encontrado.")
                return False
        except Exception as e:
            _registrar_log(f"Erro ao deletar: {e}")
            print(f"> [Oracle] Erro ao deletar: {e}")
            return False
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
    
    def obter_todos(self) -> List[Cana]:
        """Retorna todas as plantações armazenadas no Oracle."""
        if not self._ensure_connection():
            return []
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT ID, PROPRIEDADE, DATA_REGISTRO, TALHAO, RISCO_AGRONOMICO, DADOS_JSON
                FROM PLANTIO_CANA
                ORDER BY ID
            """)
            
            plantacoes = []
            for row in cursor:
                # Converte o CLOB para dicionário
                json_data = json.loads(row[5].read()) if row[5] else {}
                # Monta o dicionário completo com os dados da tabela
                dados = {
                    "id": row[0],
                    "propriedade": row[1],
                    "data": row[2].strftime("%Y-%m-%d") if row[2] else None,
                    "talhao": row[3],
                    "classificacao_risco": row[4],
                    **json_data  # sobrescreve com os dados do JSON (inclui todos os campos)
                }
                # Reconstrói o objeto Cana a partir do dicionário
                plantacoes.append(Cana.from_dict(dados))
            
            return plantacoes
        except Exception as e:
            _registrar_log(f"Erro ao buscar todas as plantações: {e}")
            print(f"> [Oracle] Erro ao buscar dados: {e}")
            return []
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
    
    def obter_por_id(self, id_registro: int) -> Optional[Cana]:
        """Retorna uma plantação específica pelo ID, ou None."""
        if not self._ensure_connection():
            return None
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT ID, PROPRIEDADE, DATA_REGISTRO, TALHAO, RISCO_AGRONOMICO, DADOS_JSON
                FROM PLANTIO_CANA
                WHERE ID = :id
            """, {"id": id_registro})
            
            row = cursor.fetchone()
            if not row:
                return None
            
            json_data = json.loads(row[5].read()) if row[5] else {}
            dados = {
                "id": row[0],
                "propriedade": row[1],
                "data": row[2].strftime("%Y-%m-%d") if row[2] else None,
                "talhao": row[3],
                "classificacao_risco": row[4],
                **json_data
            }
            return Cana.from_dict(dados)
        except Exception as e:
            _registrar_log(f"Erro ao buscar plantação por ID: {e}")
            print(f"> [Oracle] Erro ao buscar ID {id_registro}: {e}")
            return None
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
    
    def sincronizar_lote(self, lista_plantacoes: List[Cana]) -> bool:
        """
        Sincroniza um lote de plantações usando executemany para alta performance.
        """
        if not lista_plantacoes:
            return False
        
        if not self._ensure_connection():
            return False
        
        cursor = None
        try:
            # Prepara a lista de parâmetros para todas as plantações
            params_list = []
            for cultura in lista_plantacoes:
                payload = self._preparar_payload(cultura)
                json_str = json.dumps(payload, ensure_ascii=False)
                
                risco_limpo = remover_parenteses(getattr(cultura, "classificacao_risco", "NAO AVALIADO"))
                risco_limpo = remover_acentos(risco_limpo)
                
                params_list.append({
                    "id": cultura.id,
                    "prop": remover_acentos(cultura.propriedade),
                    "dt": cultura.data,
                    "talhao": remover_acentos(cultura.talhao),
                    "risco": risco_limpo,
                    "json_data": json_str
                })
            
            sql_merge = """
                MERGE INTO PLANTIO_CANA t
                USING (SELECT :id AS ID FROM DUAL) src
                ON (t.ID = src.ID)
                WHEN MATCHED THEN
                    UPDATE SET 
                        PROPRIEDADE      = :prop,
                        DATA_REGISTRO    = TO_DATE(:dt, 'YYYY-MM-DD'),
                        TALHAO           = :talhao,
                        RISCO_AGRONOMICO = :risco,
                        DADOS_JSON       = :json_data
                WHEN NOT MATCHED THEN
                    INSERT (ID, PROPRIEDADE, DATA_REGISTRO, TALHAO, RISCO_AGRONOMICO, DADOS_JSON)
                    VALUES (:id, :prop, TO_DATE(:dt, 'YYYY-MM-DD'), :talhao, :risco, :json_data)
            """
            
            cursor = self.connection.cursor()
            cursor.executemany(sql_merge, params_list)
            self.connection.commit()
            
            print(f"> [Oracle] Lote de {len(lista_plantacoes)} registros sincronizado com sucesso!")
            return True
            
        except Exception as e:
            _registrar_log(f"Erro no sincronizar_lote: {e}")
            print(f"> [Oracle] Erro na sincronização em lote: {e}")
            if self.connection:
                self.connection.rollback()
            return False
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
    
    def inicializar_estrutura(self) -> bool:
        """
        Cria a tabela PLANTIO_CANA e seus comentários, caso não exista.
        Também cria uma SEQUENCE para geração de IDs (opcional, mas recomendado).
        """
        if not self._ensure_connection():
            return False
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            
            # Verifica se a tabela existe
            cursor.execute("SELECT 1 FROM PLANTIO_CANA WHERE ROWNUM = 1")
            print("> [Oracle] Tabela PLANTIO_CANA já existe.")
            return True
            
        except oracledb.DatabaseError as e:
            error, = e.args
            if error.code == 942:  # ORA-00942: table or view does not exist
                try:
                    print("\n> [Oracle] Tabela não encontrada. Criando estrutura...")
                    
                    # Criação da tabela
                    cursor.execute("""
                        CREATE TABLE PLANTIO_CANA (
                            ID               NUMBER,
                            PROPRIEDADE      VARCHAR2(150) NOT NULL,
                            DATA_REGISTRO    DATE NOT NULL,
                            TALHAO           VARCHAR2(50) NOT NULL,
                            RISCO_AGRONOMICO VARCHAR2(50) NOT NULL,
                            DADOS_JSON       CLOB,
                            CONSTRAINT PK_PLANTIO_CANA PRIMARY KEY (ID)
                        )
                    """)
                    
                    # Comentários (Data Dictionary)
                    cursor.execute("COMMENT ON COLUMN PLANTIO_CANA.ID IS 'Identificador único sequencial da plantação (Chave Primária).'")
                    cursor.execute("COMMENT ON COLUMN PLANTIO_CANA.DATA_REGISTRO IS 'Data de inclusão do registro agronômico no sistema.'")
                    cursor.execute("COMMENT ON COLUMN PLANTIO_CANA.DADOS_JSON IS 'Carga de metadados operacionais e matemáticos higienizados em formato JSON.'")
                    
                    # Criação da SEQUENCE (opcional, mas útil)
                    try:
                        cursor.execute("""
                            CREATE SEQUENCE SEQ_PLANTIO_CANA
                            START WITH 1
                            INCREMENT BY 1
                            NOCACHE
                            NOCYCLE
                        """)
                        print("> [Oracle] Sequence SEQ_PLANTIO_CANA criada com sucesso.")
                    except oracledb.DatabaseError as seq_err:
                        # Se já existir, ignora
                        if seq_err.args[0].code != 955:  # ORA-00955: name already used
                            raise seq_err
                        else:
                            print("> [Oracle] Sequence SEQ_PLANTIO_CANA já existe.")
                    
                    self.connection.commit()
                    print("> [Oracle] Estrutura criada com sucesso!")
                    return True
                    
                except oracledb.Error as err:
                    _registrar_log(f"Erro ao criar tabela: {err}")
                    print(f"> [Oracle] Erro crítico na criação: {err}")
                    return False
            else:
                _registrar_log(f"Erro inesperado ao verificar tabela: {e}")
                print(f"> [Oracle] Erro inesperado: {e}")
                return False
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
    
    def __del__(self):
        """Garante que a conexão seja fechada ao destruir o objeto."""
        self._disconnect()