import unicodedata
from typing import Any, Dict, Union

def normalizar_string(texto: str) -> str:
    """
    Normaliza strings para comparação case-insensitive e sem acentos.
    
    """
    if not isinstance(texto, str):
        return str(texto) if texto is not None else ''
    
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf8').lower().strip()

def remover_acentos(texto: str) -> str:
    """
    Remove acentos e caracteres especiais, mantendo a capitalização original.
   
    """
    if not isinstance(texto, str):
        return str(texto) if texto is not None else ''
    
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf8')

def remover_parenteses(texto: str) -> str:
    """
    Remove tudo que estiver entre parênteses e os próprios parênteses.
    Exemplo: 'RISCO BAIXO (83.3%)' -> 'RISCO BAIXO'
    """
    if not isinstance(texto, str):
        return str(texto) if texto is not None else ''
    
    if '(' in texto:
        return texto.split('(')[0].strip()
    return texto.strip()

def sanitizar_texto_completo(texto: str) -> str:
    """
    Aplica todas as sanitizações em sequência: remove acentos, parênteses e normaliza.
    Usado para enviar dados limpos para o Oracle.
    """
    if not isinstance(texto, str):
        return str(texto) if texto is not None else ''
    
    texto = remover_parenteses(texto)
    texto = remover_acentos(texto)
    return texto.strip()

def sanitizar_payload(dados: Dict[str, Any], recursivo: bool = True) -> Dict[str, Any]:
    """
    Varre um dicionário recursivamente sanitizando todas as strings encontradas.
    Mantém números, booleanos e None intactos.
    

    """
    if not isinstance(dados, dict):
        return dados
    
    resultado = {}
    for chave, valor in dados.items():
        if isinstance(valor, str):
            resultado[chave] = sanitizar_texto_completo(valor)
        elif isinstance(valor, dict) and recursivo:
            resultado[chave] = sanitizar_payload(valor, recursivo=True)
        elif isinstance(valor, list) and recursivo:
            resultado[chave] = [
                sanitizar_payload(item, recursivo=True) if isinstance(item, dict) 
                else sanitizar_texto_completo(item) if isinstance(item, str) 
                else item
                for item in valor
            ]
        else:
            resultado[chave] = valor
    
    return resultado

def normalizar_para_comparacao(texto: str) -> str:
    """
    Combinação rápida: normaliza + remove acentos para comparações de unicidade.
    Usado pelo Gerenciador/Service para verificar se já existe cadastro.
    """
    return normalizar_string(remover_acentos(texto))