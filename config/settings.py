import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env localizado na raiz do projeto
load_dotenv()

# Constantes globais do sistema (mantidas do original)
ARQUIVO_DADOS = 'plantacoes_data.json'
ARQUIVO_LOG = 'registro_operacoes.log'

# Parâmetros de conexão Oracle agora vindos do .env
ORACLE_USER = os.getenv('ORACLE_USER', 'SEU_USUARIO_AQUI')
ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD', 'SUA_SENHA_AQUI')
ORACLE_DSN = os.getenv('ORACLE_DSN', 'SEU_DSN_AQUI')

# Parâmetros de risco (extraídos do código para centralização)
MAX_RISCO_TOTAL_ABSOLUTO = 24.0
LIMITE_SUPERIOR_SUCESSO = 99.0
MIN_RISCO_VETO = 8