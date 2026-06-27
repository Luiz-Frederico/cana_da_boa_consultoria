import math
from typing import List, Optional, Tuple, Dict, Any
from domain.models import Cana, Planta, DetalhesPlantio
from domain.dtos import RiscoResultado
from config.settings import MAX_RISCO_TOTAL_ABSOLUTO, LIMITE_SUPERIOR_SUCESSO, MIN_RISCO_VETO
from utils.sanitizer import remover_parenteses, normalizar_string, remover_acentos
from utils.classificacao import classificar_por_probabilidade


class RiskCalculator:
    """
    Responsável por calcular a pontuação de risco, classificação,
    probabilidade de sucesso e gerar os pontos de atenção.
    Toda a lógica agronômica fica isolada aqui.
    """
    
    @staticmethod
    def calcular(cultura: Cana) -> RiscoResultado:
        """
        Executa a avaliação de risco completa para uma cultura de cana.
        Retorna um DTO com todos os resultados.
        
        Esta implementação é uma cópia fiel da lógica do método
        _gerar_feedback_final da versão original do console_menu.py.
        """
        # --- Coleta de parâmetros do objeto Cana (mesmo que a versão antiga) ---
        propriedade = cultura.propriedade
        talhao = cultura.talhao
        comprimento = cultura.comprimento
        largura = cultura.largura
        tipo_terreno_original = cultura.tipo_terreno_original
        epoca_plantio = cultura.epoca_plantio
        possui_irrigacao = cultura.possui_irrigacao
        preparo_solo_seco = cultura.preparo_solo_seco
        controle_pragas = cultura.controle_pragas
        planejamento_colheita_escalonado = cultura.planejamento_colheita_escalonado
        controle_trajeto_maquinario = cultura.controle_trajeto_maquinario
        mao_de_obra_especializada = cultura.mao_de_obra_especializada
        variedades_adequadas_mecanizacao = cultura.variedades_adequadas_mecanizacao
        uso_piloto_automatico = cultura.uso_piloto_automatico
        velocidade_colhedora_acima_recomendada = cultura.velocidade_colhedora_acima_recomendada
        planta = cultura.planta
        detalhes_plantio = cultura.detalhes_plantio
        classificacao_topografica = cultura.classificacao_topografica
        classificacao_espacamento_ruas = cultura.classificacao_espacamento_ruas
        classificacao_dimensoes = cultura.classificacao_dimensoes
        classificacao_epoca = cultura.classificacao_epoca
        feedback_epoca = cultura.feedback_epoca
        tipo_terreno_original = cultura.tipo_terreno_original

        # --- Inicialização das variáveis ---
        pontuacao_risco = 0
        pontos_atencao: List[str] = []
        existe_veto_topografia = False
        veto_agronomico: Optional[str] = None

        # --- 1. Topografia (lógica idêntica à antiga) ---
        terreno_norm = normalizar_string(tipo_terreno_original)
        if terreno_norm == "plano" or terreno_norm == "levemente inclinado":
            classificacao_topografica = "Ideal (Topografia Favorável)"
        elif terreno_norm == "acidentado":
            pontuacao_risco += 5
            existe_veto_topografia = True
            classificacao_topografica = "Alto Risco (Inviável para Máquinas)"
            pontos_atencao.append("TOPOGRAFIA: Tipo de terreno: Acidentado (+5 Pontos de Risco)")
        else:
            pontuacao_risco += 3
            classificacao_topografica = "Desconhecida (Verificar)"
            pontos_atencao.append(f"TOPOGRAFIA: Tipo de terreno desconhecido '{tipo_terreno_original}' (+3 Pontos de Risco)")

        # --- 2. Método de plantio MPB (subadensamento/superadensamento) ---
        if detalhes_plantio and detalhes_plantio.metodo == 'MPB':
            try:
                esp_str = detalhes_plantio.detalhe_principal.split(' ')[0].replace(',', '.')
                esp_plantas = float(esp_str)
                if esp_plantas > 1.0:
                    pontuacao_risco += 10
                    pontos_atencao.append(f"PLANTIO MPB (SUBADENSAMENTO): Distância entre plantas > 1.0m. (+10 Pontos de Risco)")
                elif esp_plantas < 0.5:
                    pontuacao_risco += 7
                    pontos_atencao.append(f"PLANTIO MPB (SUPERADENSAMENTO): Distância entre plantas < 0.5m. (+7 Pontos de Risco)")
            except Exception:
                pass

        # --- 3. Época de plantio (lógica idêntica à antiga) ---
        mes_norm = normalizar_string(epoca_plantio)
        if mes_norm in ['janeiro', 'fevereiro', 'marco', 'abril']:
            classificacao_epoca = "Outra Época (Risco Moderado)"
            pontuacao_risco += 1
            feedback_epoca = "Plantio regular. Condições climáticas estáveis, risco padrão de estabelecimento."
        elif mes_norm in ['maio', 'junho', 'julho', 'agosto']:
            classificacao_epoca = "Plantio de Inverno em Sequeiro (Alto Risco)"
            pontuacao_risco += 8
            feedback_epoca = (
                "Sistema de **Alto Risco Agronômico** (Ciclo 12 meses - Cana de Ano).\n"
                "Efeitos Negativos: Brotação e estabelecimento inicial ocorrem no período seco e sob temperaturas baixas, "
                "levando a alto risco de falhas e crescimento lento.\n"
                "Resultado: Baixa produtividade inicial (TCH) e risco de perda de estande. Atenção: Este plantio só é viável quando há IRRIGAÇÃO complementar."
            )
            pontos_atencao.append(f"ÉPOCA PLANTIO: {feedback_epoca} (+8 Pontos de Risco)")
        elif mes_norm in ['setembro', 'outubro', 'novembro', 'dezembro']:
            classificacao_epoca = "Plantio de Ano-e-Meio (Excelente Janela)"
            feedback_epoca = "Excelente janela de plantio (Ciclo 18 meses). Ótimo acúmulo térmico e hídrico para o desenvolvimento radicular."
        else:
            classificacao_epoca = "Mês Inválido ou Não Informado"
            pontuacao_risco += 4
            feedback_epoca = "Época de plantio desconhecida ou não informada."
            pontos_atencao.append("ÉPOCA PLANTIO: Mês não reconhecido (+4 Pontos de Risco)")

        cultura.classificacao_topografica = classificacao_topografica
        cultura.classificacao_epoca = classificacao_epoca
        cultura.feedback_epoca = feedback_epoca

        # --- 4. Dimensões (lógica idêntica à antiga) ---
        classificacao_dimensoes = "Ideal"
        feedback_dimensoes = "As dimensões do talhão estão dentro dos parâmetros ideais."
        if comprimento < 500:
            classificacao_dimensoes = "Não Ideal (Risco de Prejuízo)"
            feedback_dimensoes = "Comprimento abaixo de 500m. Alto risco de prejuízo devido ao excesso de carreadores e tempo de manobra."
        elif comprimento >= 801:
            classificacao_dimensoes = "Não Ideal (Risco de Prejuízo)"
            feedback_dimensoes = "Comprimento acima de 800m. Risco de prejuízo logístico e operacional significativo no plantio e colheita."
        elif 700 < comprimento <= 800:
            classificacao_dimensoes = "Requer Cuidados"
            feedback_dimensoes = "Comprimento acima de 700m e até 800m. Requer atenção no manejo devido à possível perda de eficiência."

        largura_ideal = comprimento / 2
        tolerancia = 0.10
        largura_min = largura_ideal * (1 - tolerancia)
        largura_max = largura_ideal * (1 + tolerancia)

        if not (largura_min <= largura <= largura_max):
            if classificacao_dimensoes == "Ideal":
                classificacao_dimensoes = "Requer Cuidados"
                feedback_dimensoes = f"A largura ({largura:.2f} m) está fora da faixa ideal (L / 2 ± 10%). A largura ideal seria entre {largura_min:.2f} m e {largura_max:.2f} m."
            elif classificacao_dimensoes != "Não Ideal (Risco de Prejuízo)":
                feedback_dimensoes += f" [ALERTA] Largura fora da faixa ideal de 10% ({largura_min:.2f} m e {largura_max:.2f} m)."
            elif classificacao_dimensoes == "Não Ideal (Risco de Prejuízo)":
                feedback_dimensoes += f" [ALERTA] Largura também fora da faixa ideal de 10% ({largura_min:.2f} m e {largura_max:.2f} m)."

        if classificacao_dimensoes == "Não Ideal (Risco de Prejuízo)":
            pontuacao_risco += 2
            pontos_atencao.append(f"DIMENSOES (COMPRIMENTO): {feedback_dimensoes} (+2 Pontos de Risco)")
        elif classificacao_dimensoes == "Requer Cuidados":
            pontuacao_risco += 1
            pontos_atencao.append(f"DIMENSOES (LARGURA/COMPRIMENTO): {feedback_dimensoes} (+1 Ponto de Risco)")

        cultura.classificacao_dimensoes = classificacao_dimensoes

        # --- 5. Espaçamento de ruas (CORRIGIDO com feedback definido) ---
        if planta:
            esp = planta.espacamento_ruas
            if 1.5 <= esp <= 1.8:
                classificacao_espacamento_ruas = "Ideal"
                feedback_espacamento_ruas = "Espaçamento entre 1,5m e 1,8m. Ideal para colheita mecanizada, minimizando pisoteio e compactação."
                # Não adiciona pontos
            elif esp < 1.5:
                classificacao_espacamento_ruas = "Não Ideal"
                feedback_espacamento_ruas = f"Espaçamento ({esp:.2f}m) menor que 1,5m. Causa dano à soqueira e compactação, reduzindo a produtividade dos cortes subsequentes."
                pontuacao_risco += 2
                pontos_atencao.append(f"ESPAÇAMENTO RUAS: {feedback_espacamento_ruas} (+2 Pontos de Risco)")
            else:  # esp > 1.8
                classificacao_espacamento_ruas = "Não Ideal"
                feedback_espacamento_ruas = f"Espaçamento ({esp:.2f}m) maior que 1,8m. Causa baixa densidade de plantas, favorece plantas daninhas e resulta em uso ineficiente da terra."
                pontuacao_risco += 2
                pontos_atencao.append(f"ESPAÇAMENTO RUAS: {feedback_espacamento_ruas} (+2 Pontos de Risco)")

            cultura.classificacao_espacamento_ruas = classificacao_espacamento_ruas
        else:
            cultura.classificacao_espacamento_ruas = "Não informado"

        # --- 6. Fatores de manejo (Bônus e Riscos) - IDÊNTICO À VERSÃO ANTIGA ---
        # Irrigação
        if possui_irrigacao:
            pontuacao_risco -= 2
            pontos_atencao.insert(0, "IRRIGAÇÃO (BÔNUS): Manejo hídrico eficiente reduz o risco de estresse. (-2 Pontos de Risco)")
        else:
            pontuacao_risco += 1
            pontos_atencao.append("IRRIGAÇÃO (RISCO): Não há irrigação complementar. Aumenta a dependência da chuva. (+1 Ponto de Risco)")

        # Preparo do solo na seca
        if preparo_solo_seco:
            pontuacao_risco -= 1
            pontos_atencao.insert(0, "PREPARO SOLO SECA (BÔNUS): Descompactação adequada. (-1 Ponto de Risco)")
        else:
            pontuacao_risco += 3
            pontos_atencao.append("PREPARO SOLO (RISCO PONDERADO): Falta de preparo descompactante. Compactação inibe o desenvolvimento radicular. (+3 Pontos de Risco)")

        # Controle de pragas
        if controle_pragas:
            pontuacao_risco -= 1
            pontos_atencao.insert(0, "CONTROLE PRAGAS (BÔNUS): Práticas fitossanitárias. (-1 Ponto de Risco)")
        else:
            pontuacao_risco += 1
            pontos_atencao.append("CONTROLE PRAGAS (RISCO): Falta de controle fitossanitário. (+1 Ponto de Risco)")

        # Planejamento colheita escalonado
        if planejamento_colheita_escalonado:
            pontuacao_risco -= 1
            pontos_atencao.insert(0, "PLANEJAMENTO ESCALONADO (BÔNUS): Colheita na melhor janela. (-1 Ponto de Risco)")
        else:
            pontuacao_risco += 1
            pontos_atencao.append("PLANEJAMENTO ESCALONADO (RISCO): Risco de colheita tardia/maturação inadequada. (+1 Ponto de Risco)")

        # Controle de tráfego e piloto automático
        if controle_trajeto_maquinario and uso_piloto_automatico:
            pontuacao_risco -= 2
            pontos_atencao.insert(0, "CONTROLE TRÁFEGO + PILOTO (BÔNUS): Reduz a compactação e maximiza a precisão. (-2 Pontos de Risco)")
        elif controle_trajeto_maquinario or uso_piloto_automatico:
            pontuacao_risco -= 1
            pontos_atencao.insert(0, "CONTROLE TRÁFEGO OU PILOTO (BÔNUS): Algum controle de tráfego/precisão existe. (-1 Ponto de Risco)")
        else:
            pontuacao_risco += 3
            pontos_atencao.append("CONTROLE TRÁFEGO (RISCO PONDERADO): Ausência de controle de tráfego (linhas e piloto) gera compactação aleatória. (+3 Pontos de Risco)")
            if not controle_trajeto_maquinario:
                pontos_atencao.append("FATOR DETALHE: Sem Controle no Trajeto Maquinário.")
            if not uso_piloto_automatico:
                pontos_atencao.append("FATOR DETALHE: Sem Piloto Automático/GPS.")

        # Mão de obra especializada
        if mao_de_obra_especializada:
            pontuacao_risco -= 1
            pontos_atencao.insert(0, "MÃO DE OBRA (BÔNUS): Reduz o risco de perdas operacionais. (-1 Ponto de Risco)")
        else:
            pontuacao_risco += 1
            pontos_atencao.append("MÃO DE OBRA (RISCO): Mão de obra não especializada. (+1 Ponto de Risco)")

        # Variedades adequadas à mecanização
        if variedades_adequadas_mecanizacao:
            pontuacao_risco -= 1
            pontos_atencao.insert(0, "VARIEDADES (BÔNUS): Variedades eretas e uniformes. (-1 Ponto de Risco)")
        else:
            pontuacao_risco += 1
            pontos_atencao.append("VARIEDADES (RISCO): Uso de variedades inadequadas. (+1 Ponto de Risco)")

        # Velocidade colhedora acima do recomendado
        if velocidade_colhedora_acima_recomendada:
            pontuacao_risco += 5
            pontos_atencao.append("VELOCIDADE COLHEDORA (VETO PONDERADO): Velocidade excessiva eleva drasticamente as perdas, dano à soqueira. (+5 Pontos de Risco)")

        # --- 7. Ajuste final (veto topografia e correção lógica) ---
        risco_final = max(0, pontuacao_risco)
        MIN_RISCO_VETO = 8
        veto_agronomico = None
        if existe_veto_topografia and risco_final < MIN_RISCO_VETO:
            risco_final = MIN_RISCO_VETO
            veto_agronomico = f"VETO TOPOGRAFIA: Risco ajustado para {MIN_RISCO_VETO} (RISCO ALTO). Topografia ACIDENTADA não pode ser compensada por bônus de manejo."

        # Correção lógica: se risco_final == 0 e algum fator de manejo estiver False
        if (risco_final == 0) and (not possui_irrigacao or not preparo_solo_seco or not controle_pragas or not planejamento_colheita_escalonado or not controle_trajeto_maquinario):
            risco_final = 1
            pontos_atencao.append("AVISO (CORREÇÃO LÓGICA): O Risco foi ajustado para 1. O manejo incompleto impede a classificação RISCO MÍNIMO (Risco 0).")

        # --- 8. Cálculo da probabilidade (idêntico à antiga) ---
        MAX_RISCO_TOTAL_ABSOLUTO = 24.0
        prob_sucesso = max(0.0, 100.0 - ((100.0 * risco_final) / MAX_RISCO_TOTAL_ABSOLUTO))
        prob_sucesso = min(prob_sucesso, 99.0)  # Cap em 99.0 como na antiga

        # --- 9. Classificação do risco (usa a função baseada em probabilidade) ---
        classificacao_base = classificar_por_probabilidade(prob_sucesso)
        classificacao_risco = f"{classificacao_base} ({risco_final} pts, {prob_sucesso:.1f}%)"

        # Aplica sanitização
        classificacao_risco = remover_parenteses(classificacao_risco)
        classificacao_risco = remover_acentos(classificacao_risco)

        # --- 10. Atualiza os atributos do objeto cultura ---
        cultura.pontuacao_risco = risco_final
        cultura.classificacao_risco = classificacao_risco
        cultura.probabilidade_sucesso = f"{prob_sucesso:.1f}%"
        cultura.pontos_atencao = pontos_atencao
        cultura.veto_agronomico = veto_agronomico

        # --- 11. Retorna o DTO ---
        return RiscoResultado(
            pontuacao=risco_final,
            classificacao=classificacao_risco,
            probabilidade_sucesso=f"{prob_sucesso:.1f}%",
            pontos_atencao=pontos_atencao,
            veto_agronomico=veto_agronomico
        )