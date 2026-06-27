import datetime
from config.settings import ARQUIVO_LOG

def _registrar_log(mensagem: str):
    """
    Registra uma mensagem com timestamp no arquivo de log.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {mensagem}\n"
    try:
        with open(ARQUIVO_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except IOError as e:
        print(f"> ERRO ao gravar log: {e}")