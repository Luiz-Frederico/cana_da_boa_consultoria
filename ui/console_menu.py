import getpass
from typing import Optional, Dict, Any, Tuple, List
from domain.models import Planta, DetalhesPlantio, Cana
from domain.risk_calculator import RiskCalculator
from domain.dtos import RiscoResultado
from repositories.json_repository import JsonRepository
from repositories.oracle_repository import OracleRepository
from services.plantacao_service import PlantacaoService
from utils.sanitizer import normalizar_string, remover_acentos
import config.settings as settings
from utils.helpers import _registrar_log


def solicitar_e_conectar_oracle(service: PlantacaoService) -> bool:
    """
    Gerencia a conexão inicial com o Oracle, salvando credenciais dinamicamente
    e validando a inicialização da infraestrutura e sincronização em lote.
    """
    print("\n" + "=" * 50)
    print("### CONEXÃO INICIAL COM BANCO DE DADOS ORACLE ###")
    print("=" * 50)
    
    # Pergunta Inicial Obrigatória
    if not _obter_input_sim_nao("Deseja configurar e conectar ao Oracle agora?"):
        print("> Conexão Oracle adiada. Use a opção 6 no menu para conectar mais tarde.")
        return False
        
    print("\n--- Credenciais de Conexão ---")
    user = input("Digite o Usuário (ex: SYSTEM): ")
    try:
        password = getpass.getpass("Digite a Senha: ")
    except Exception:
        print("Aviso: Falha ao esconder a senha. A senha será exibida no input.")
        password = input("Digite a Senha: ")
    dsn = input("Digite o DSN/String de Conexão (ex: localhost:1521/xe): ")

    # Conecta via Service
    conectado = service.conectar_oracle(user, password, dsn)
    
    if conectado:
        # Requisito 1: Criar/Validar a tabela automaticamente após conectar
        infra_pronta = service.inicializar_infraestrutura_oracle()
        
        if infra_pronta:
            # Requisito 2: Mensagem 1 - Autorização para enviar os dados locais do JSON
            if _obter_input_sim_nao("\nDeseja enviar os dados locais do JSON para o Oracle?"):
                service.sincronizar_todos()
            else:
                print("> Sincronização em lote pulada pelo usuário.")

            # Requisito 2: Mensagem 2 - Autorização para enviar futuros novos cadastros
            print("\n==================================================")
            if _obter_input_sim_nao("Deseja enviar os dados dos registros cadastrados para o Oracle?"):
                print("> Modo Sincronizado Ativo: Novos cadastros serão espelhados em tempo real na nuvem.")
            else:
                print("> Aviso: A aplicação continuará conectada, mas o espelhamento em tempo real foi recusado.")
                
        return True
    return False


def _obter_input_sim_nao(prompt: str) -> bool:
    """Laço para garantir que o input do usuário seja Sim ou Não, retornando True/False."""
    while True:
        resposta = input(f"{prompt} (S/N): ")
        resposta_norm = normalizar_string(resposta)
        if resposta_norm in ['s', 'sim']:
            return True
        elif resposta_norm in ['n', 'nao']:
            return False
        else:
            print("> Resposta inválida. Por favor, digite Sim (S) ou Não (N).")


class Menu:
    def __init__(self):
        # Inicializa a nova arquitetura
        json_repo = JsonRepository()
        oracle_repo = OracleRepository()
        self._service = PlantacaoService(json_repo, oracle_repo)
        
        self._opcoes = {
            '1': ('Adicionar Plantação', self._adicionar_plantacao),
            '2': ('Listar Plantações', self._listar_plantacoes),
            '3': ('Atualizar Plantação', self._atualizar_plantacao),
            '4': ('Deletar Plantação', self._deletar_plantacao),
            '5': ('Salvar Dados (JSON)', self._salvar_dados_json),
            '6': ('Conectar Banco de Dados Oracle', self._conectar_oracle),
            '7': ('Sair', self._sair)
        }
        self.meses_validos = {
            "janeiro": "jan", "fevereiro": "fev", "março": "mar", "abril": "abr",
            "maio": "mai", "junho": "jun", "julho": "jul", "agosto": "ago",
            "setembro": "set", "outubro": "out", "novembro": "nov", "dezembro": "dez"
        }
    
    def get_service(self):
        """Retorna o service para uso externo (ex: conexão inicial)."""
        return self._service    

    # --- Métodos auxiliares de validação e coleta  ---

    def _obter_input_numerico(self, prompt: str) -> float:
        while True:
            try:
                input_str = input(prompt).replace(',', '.')
                valor = float(input_str)
                if valor <= 0:
                    print("> Entrada inválida. Por favor, digite um número positivo.")
                    continue
                return valor
            except ValueError:
                print("> Entrada inválida. Por favor, digite um número.")

    def _validar_espacamento_ruas(self, espacamento: float) -> Tuple[str, str]:
        if 1.5 <= espacamento <= 1.8:
            classificacao = "Ideal"
            feedback = "Espaçamento entre 1,5m e 1,8m. Ideal para colheita mecanizada, minimizando pisoteio e compactação."
        elif espacamento < 1.5:
            classificacao = "Não Ideal"
            feedback = f"Espaçamento ({espacamento:.2f}m) menor que 1,5m. Causa dano à soqueira e compactação, reduzindo a produtividade dos cortes subsequentes."
        else:
            classificacao = "Não Ideal"
            feedback = f"Espaçamento ({espacamento:.2f}m) maior que 1,8m. Causa baixa densidade de plantas, favorece plantas daninhas e resulta em uso ineficiente da terra."
        return classificacao, feedback

    def _validar_dimensoes_cana(self, comprimento: float, largura: float) -> Tuple[str, str]:
        classificacao = "Ideal"
        feedback = "As dimensões do talhão estão dentro dos parâmetros ideais."
        if comprimento < 500:
            classificacao = "Não Ideal (Risco de Prejuízo)"
            feedback = "Comprimento abaixo de 500m. Alto risco de prejuízo devido ao excesso de carreadores e tempo de manobra."
        elif comprimento >= 801:
            classificacao = "Não Ideal (Risco de Prejuízo)"
            feedback = "Comprimento acima de 800m. Risco de prejuízo logístico e operacional significativo no plantio e colheita."
        elif 700 < comprimento <= 800:
            classificacao = "Requer Cuidados"
            feedback = "Comprimento acima de 700m e até 800m. Requer atenção no manejo devido à possível perda de eficiência."

        largura_ideal = comprimento / 2
        tolerancia = 0.10
        largura_min = largura_ideal * (1 - tolerancia)
        largura_max = largura_ideal * (1 + tolerancia)

        if not (largura_min <= largura <= largura_max):
            if classificacao == "Ideal":
                classificacao = "Requer Cuidados"
                feedback = f"A largura ({largura:.2f} m) está fora da faixa ideal (L / 2 ± 10%). A largura ideal seria entre {largura_min:.2f} m e {largura_max:.2f} m."
            elif classificacao != "Não Ideal (Risco de Prejuízo)":
                feedback += f" [ALERTA] Largura fora da faixa ideal de 10% ({largura_min:.2f} m e {largura_max:.2f} m)."
            elif classificacao == "Não Ideal (Risco de Prejuízo)":
                feedback += f" [ALERTA] Largura também fora da faixa ideal de 10% ({largura_min:.2f} m e {largura_max:.2f} m)."
        return classificacao, feedback

    def _classificar_terreno(self, tipo_terreno: str) -> str:
        terreno_norm = normalizar_string(tipo_terreno)
        if terreno_norm in ["plano", "levemente inclinado"]:
            return "Ideal (Topografia Favorável)"
        elif terreno_norm == "acidentado":
            return "Alto Risco (Inviável para Máquinas)"
        else:
            return "Desconhecida (Verificar)"

    def _logica_plantio_toletes(self) -> DetalhesPlantio:
        print("\n--- Modo Plantio com Tolete (T) ---")
        gemas = self._obter_input_numerico("Digite a quantidade de gemas viáveis por metro linear de sulco: ")
        while True:
            qualidade_input = input("A muda é de boa qualidade (Sim / Não)? ")
            qualidade_norm = normalizar_string(qualidade_input)
            if qualidade_norm in ['sim', 's']:
                boa_qualidade = True
                break
            elif qualidade_norm in ['nao', 'n']:
                boa_qualidade = False
                break
            else:
                print("> Opção inválida. Digite Sim ou Não.")

        classificacao = ""
        feedback = ""
        PADRAO_MINIMO = 12
        DENSIDADE_ESTRESSE = 15

        if gemas < PADRAO_MINIMO:
            classificacao = "Alto Risco de Falha"
            feedback = f"Densidade ({gemas} gemas/m) abaixo do padrão mínimo de 12 gemas/m. Risco elevado de falhas no estande e necessidade de replantio. Considere sobreposição maior dos toletes."
        elif PADRAO_MINIMO <= gemas <= 14:
            if not boa_qualidade:
                classificacao = "Risco de Falha (Requer Overplant)"
                feedback = f"Densidade ({gemas} gemas/m) baixa para má qualidade. Em estresse hídrico ou com muda de baixa qualidade, recomenda-se Overplant (15 a 18 gemas/m) para compensar falhas de brotação. Risco de fitossanidade se a muda for de canavial velho (viveiro)."
            else:
                classificacao = "Padrão Mínimo (Aceitável)"
                feedback = f"Densidade ({gemas} gemas/m) atinge o Padrão de Qualidade Mínimo (12 gemas/m). Garante uma população inicial robusta de colmos."
        elif gemas >= DENSIDADE_ESTRESSE:
            if not boa_qualidade:
                classificacao = "Recomendado em Estresse"
                feedback = f"Densidade ({gemas} gemas/m) é ideal para condições de estresse (seca) ou muda de baixa qualidade (15 a 18 gemas/m). Ajuda a compensar possíveis falhas na brotação."
            else:
                classificacao = "Padrão Robusto"
                feedback = f"Densidade ({gemas} gemas/m) é um padrão robusto (15 a 18 gemas/m). Aumenta a segurança para condições de plantio em estiagem ou se a qualidade da muda for duvidosa, minimizando a baixa taxa de brotação."

        detalhe_principal = f"{gemas} gemas/m | Qualidade: {'Boa' if boa_qualidade else 'Baixa'}"
        return DetalhesPlantio(metodo='Toletes', detalhe_principal=detalhe_principal, classificacao=classificacao, feedback=feedback)

    def _logica_plantio_mpb(self) -> DetalhesPlantio:
        print("\n--- Modo Mudas Pré-Brotadas (MPB) ---")
        espacamento_plantas = self._obter_input_numerico("Digite o espaçamento entre as plantas na linha (em metros): ")
        classificacao = ""
        feedback = ""
        if 0.50 <= espacamento_plantas <= 1.0:
            classificacao = "Ideal (Alta Uniformidade)"
            feedback = (
                f"O espaçamento ({espacamento_plantas:.2f} m) está no range ideal (0,50 m a 1,0 m), buscando o equilíbrio entre competição inicial por recursos e rápido fechamento do dossel."
                "O MPB garante uniformidade, minimiza falhas e o risco fitossanitário é menor."
            )
        elif espacamento_plantas < 0.50:
            classificacao = "Superadensamento (Alto Risco)"
            feedback = (
                f"Distância ({espacamento_plantas:.2f} m) menor que 0,50 m. Isso leva a uma população excessiva de touceiras (> 20.000/ha) e **superadensamento**."
                "Efeitos Negativos: Aumento do Custo de Plantio, forte competição por recursos, resultando em estiolamento e colmos mais finos/frágeis, o que Reduz a Qualidade dos Colmos."
            )
        else:
            classificacao = "Subadensamento (Alto Risco)"
            feedback = (
                f"Distância ({espacamento_plantas:.2f} m) maior que 1,0 m. Isso leva ao **subadensamento** e a uma população insuficiente de touceiras (< 18.000/ha)."
                "Efeitos Negativos: Baixa Eficiência de Área e perda de potencial produtivo (menor TCH). O Atraso no Fechamento do Dossel favorece plantas daninhas, exigindo Aumento nos Custos de Manejo."
            )
        detalhe_principal = f"{espacamento_plantas:.2f} m entre plantas"
        return DetalhesPlantio(metodo='MPB', detalhe_principal=detalhe_principal, classificacao=classificacao, feedback=feedback)

    def _logica_epoca_plantio(self) -> Tuple[str, str, str]:
        while True:
            epoca_input = input("Digite a época de plantio (Mês, ex: janeiro, maio): ")
            epoca_norm = normalizar_string(epoca_input)
            mes_completo = None
            for nome_completo_original in self.meses_validos.keys():
                nome_completo_norm = normalizar_string(nome_completo_original)
                if epoca_norm == nome_completo_norm or epoca_norm == self.meses_validos[nome_completo_original]:
                    mes_completo = nome_completo_original
                    break
            if mes_completo:
                mes_norm = normalizar_string(mes_completo)
                break
            else:
                print("\n> Mês inválido. Por favor, digite um mês válido (ex: janeiro, fevereiro, março).")

        classificacao = ""
        feedback = ""
        if mes_norm in ['janeiro', 'fevereiro', 'marco']:
            classificacao = "Cana de Ano e Meio (Otimização)"
            feedback = (
                "Sistema de Alta Rentabilidade (Ciclo 18 meses).\n"
                "Efeitos Positivos: Plantio em condições ideais de umidade/temperatura (verão/outono), garantindo brotação rápida e uniforme. A fase de crescimento máximo coincide com o 2º período chuvoso.\n"
                "Resultado: Alta Produtividade (TCH) e Máximo acúmulo de ATR (maturação natural na seca) na primeira safra. **Recomendação Principal**."
            )
        elif mes_norm in ['maio', 'junho', 'julho', 'agosto']:
            classificacao = "Plantio de Inverno em Sequeiro (Alto Risco)"
            feedback = (
                "Sistema de **Alto Risco Agronômico** (Ciclo 12 meses - Cana de Ano).\n"
                "Efeitos Negativos: Brotação e estabelecimento inicial ocorrem no período seco e sob temperaturas baixas, levando a alto risco de falhas e crescimento lento.\n"
                "Resultado: Baixa produtividade inicial (TCH) e risco de perda de estande. Atenção: Este plantio só é viável quando há IRRIGAÇÃO complementar."
            )
        else:
            classificacao = "Outra Época (Risco Moderado)"
            feedback = (
                "Esta época de plantio foge dos sistemas principais e apresenta risco moderado.\n"
                "Atenção: É fundamental avaliar a previsão climática para o seu ciclo. Há risco de Estresse Hídrico Severo na fase de crescimento máximo ou de Estresse por Temperatura Baixa/Geada na brotação."
            )
        return mes_completo.capitalize(), classificacao, feedback

    def _formatar_tabela_classificacao(self) -> str:
        return (
                "\n" + "=" * 95 +
                "\n### TABELA DE REFERÊNCIA DE PROBABILIDADE DE SUCESSO E RISCO ###\n" +
                "=" * 95 +
                "\n| Pontuação de Risco (Aproximada) | Range de Probabilidade (Sucesso) | Classificação de Risco |\n" +
                "|:-------------------------------:|:--------------------------------:|:-----------------------|\n" +
                "| 0                               | 96% - 99%                        | RISCO MINIMO           |\n" +
                "| 1 a 2                           | 86% - 95%                        | RISCO MUITO BAIXO      |\n" +
                "| 3 a 5                           | 76% - 85%                        | RISCO BAIXO            |\n" +
                "| 6 a 8                           | 67% - 75%                        | RISCO MEDIO/BAIXO      |\n" +
                "| 9 a 12                          | 51% - 66%                        | RISCO MEDIO            |\n" +
                "| 13 a 18                         | 31% - 50%                        | RISCO ALTO             |\n" +
                "| > 18                            | 0% - 30%                         | RISCO ALTISSIMO        |\n" +
                "=" * 95 + "\n"
        )

    # --- Método principal de criação (agora usa RiskCalculator) ---

    def _selecionar_cultura_para_criar(self, indice_atual: Optional[int] = None) -> Optional[Cana]:
        propriedade = input("Digite o nome da propriedade: ")
        if not propriedade: return None
        while True:
            talhao = input(f"Digite a identificação do talhão para '{propriedade}' (nome ou número): ")
            if not talhao: continue
            erro = self._service.verificar_unicidade(propriedade, talhao, indice_atual)
            if erro: print(f"\n> ERRO DE CADASTRO: {erro}")
            else: break

        MAPA_TERRENO = {'1': 'plano', '2': 'levemente inclinado', '3': 'acidentado'}
        OPCOES_TERRENO_VALIDAS = ["plano", "levemente inclinado", "acidentado"]
        while True:
            tipo_terreno_input = input("Informe o tipo do terreno (plano (1), levemente inclinado (2) ou acidentado(3)): ")
            tipo_terreno_original = MAPA_TERRENO.get(tipo_terreno_input, tipo_terreno_input)
            terreno_norm = normalizar_string(tipo_terreno_original)
            if terreno_norm in OPCOES_TERRENO_VALIDAS:
                classificacao_topografica = self._classificar_terreno(terreno_norm)
                break
            else: print("\n> Opção inválida. Tente novamente (use 1, 2, 3 ou o nome completo).")

        espacamento_ruas = self._obter_input_numerico("Digite o espaçamento entre as RUAS (em metros): ")
        classificacao_espacamento_ruas, feedback_espacamento_ruas = self._validar_espacamento_ruas(espacamento_ruas)
        planta = Planta(espacamento_ruas)

        espacamento_plantas_mpb = 0.0
        while True:
            metodo_plantio_input = input("Método de plantio toletes(T) ou mudas-pré brotadas(M)? ")
            metodo_plantio_norm = normalizar_string(metodo_plantio_input)
            if metodo_plantio_norm in ['t', 'toletes']:
                detalhes_plantio_obj = self._logica_plantio_toletes()
                break
            elif metodo_plantio_norm in ['m', 'mudas', 'mudas-pre brotadas', 'mpb']:
                detalhes_plantio_obj = self._logica_plantio_mpb()
                try:
                    espacamento_str = detalhes_plantio_obj.detalhe_principal.split(' ')[0].replace(',', '.')
                    espacamento_plantas_mpb = float(espacamento_str)
                except Exception: pass
                break
            else: print("\n> Opção inválida. Digite T-toletes / M - mudas-pré brotadas.")
        
        detalhes_plantio = detalhes_plantio_obj
        epoca_plantio, classificacao_epoca, feedback_epoca = self._logica_epoca_plantio()
        comprimento = self._obter_input_numerico("Digite o comprimento do terreno (m): ")
        largura = self._obter_input_numerico("Digite a largura do terreno (m): ")
        classificacao_dimensoes, feedback_dimensoes = self._validar_dimensoes_cana(comprimento, largura)

        print("\n--- Fatores Adicionais de Manejo (Sim/Não) ---")
        possui_irrigacao = _obter_input_sim_nao("O talhão possui irrigação complementar (salvamento/fertirrigação)?")
        preparo_solo_seco = _obter_input_sim_nao("Foi realizado preparo do solo (escarificação/subsolagem) em período de seca para quebra de compactação?")
        controle_pragas = _obter_input_sim_nao("Existe controle de pragas, doenças e ervas daninhas?")
        planejamento_colheita_escalonado = _obter_input_sim_nao("O planejamento da colheita ocorre de forma escalonada?")
        controle_trajeto_maquinario = _obter_input_sim_nao("Possui controle no trajeto do maquinário? (ex: linha de plantio definida)")
        mao_de_obra_especializada = _obter_input_sim_nao("Utiliza mão de obra especializada para a colheita de cana mecanizada?")
        variedades_adequadas_mecanizacao = _obter_input_sim_nao("Utiliza variedades de cana-de-açúcar que sejam adequadas à mecanização? (ex: eretas)")
        uso_piloto_automatico = _obter_input_sim_nao("Utiliza uso de piloto automático ou GPS para auxiliar o controle de tráfego do maquinário?")
        velocidade_colhedora_acima_recomendada = _obter_input_sim_nao("Utiliza na colhedora velocidade acima das recomendadas pelo fabricante?")

        # Cria o objeto Cana com os dados coletados
        nova_cultura = Cana(
            propriedade, talhao, comprimento, largura, planta, classificacao_dimensoes,
            classificacao_topografica, classificacao_espacamento_ruas, detalhes_plantio,
            epoca_plantio, classificacao_epoca, feedback_epoca,
            tipo_terreno_original, possui_irrigacao, preparo_solo_seco,
            controle_pragas, planejamento_colheita_escalonado, controle_trajeto_maquinario,
            mao_de_obra_especializada, variedades_adequadas_mecanizacao, uso_piloto_automatico,
            velocidade_colhedora_acima_recomendada
        )

        # --- CÁLCULO DE RISCO (agora via RiskCalculator) ---
        resultado: RiscoResultado = RiskCalculator.calcular(nova_cultura)
        nova_cultura.pontuacao_risco = resultado.pontuacao
        nova_cultura.classificacao_risco = resultado.classificacao
        nova_cultura.probabilidade_sucesso = resultado.probabilidade_sucesso
        nova_cultura.pontos_atencao = resultado.pontos_atencao
        nova_cultura.veto_agronomico = resultado.veto_agronomico

        # --- EXIBIÇÃO DO RESUMO (mantida intacta) ---
        print("\n" + "=" * 80)
        print(f"RESUMO DAS CLASSIFICAÇÕES INDIVIDUAIS para {propriedade} - {talhao}")
        print("=" * 80)
        print(f"> TOPOGRAFIA DO TERRENO: {tipo_terreno_original.upper()} (Classificação: {classificacao_topografica})")
        print(f"\n> CLASSIFICAÇÃO ESPAÇAMENTO RUAS: {classificacao_espacamento_ruas.upper()}")
        print(f"> Feedback: {feedback_espacamento_ruas}")
        print(f"\n> MÉTODO DE PLANTIO ({detalhes_plantio.metodo.upper()}): {detalhes_plantio.classificacao.upper()}")
        print(f"> Detalhe: {detalhes_plantio.detalhe_principal}")
        print(f"> Feedback: {detalhes_plantio.feedback}")
        print(f"\n> ÉPOCA DE PLANTIO ({epoca_plantio.upper()}): {classificacao_epoca.upper()}")
        print(f"> Feedback: {feedback_epoca}")
        print(f"\n> CLASSIFICAÇÃO DIMENSÕES: {classificacao_dimensoes.upper()}")
        print(f"> Feedback: {feedback_dimensoes}")

        print("\n--- FATORES DE MANEJO ---")
        print(f"> Irrigação Complementar: {'Sim' if possui_irrigacao else 'Não'}")
        print(f"> Preparo do Solo na Seca: {'Sim' if preparo_solo_seco else 'Não'}")
        print(f"> Controle de Pragas, Doenças e Ervas Daninhas: {'Sim' if controle_pragas else 'Não'}")
        print(f"> Planejamento da Colheita Escalonado: {'Sim' if planejamento_colheita_escalonado else 'Não'}")
        print(f"> Controle no Trajeto do Maquinário: {'Sim' if controle_trajeto_maquinario else 'Não'}")
        print(f"> Mão de Obra Especializada: {'Sim' if mao_de_obra_especializada else 'Não'}")
        print(f"> Variedades Adequadas à Mecanização: {'Sim' if variedades_adequadas_mecanizacao else 'Não'}")
        print(f"> Uso de Piloto Automatico/GPS: {'Sim' if uso_piloto_automatico else 'Não'}")
        print(f"> Velocidade Colhedora Acima da Recomendada: {'Sim' if velocidade_colhedora_acima_recomendada else 'Não'}")
        print("-" * 80)

        print("\n" + "=" * 80)
        print(f"### FEEDBACK FINAL CONSOLIDADO (RISCO AGRONÔMICO) ###")
        print("=" * 80)
        print(f"PONTUAÇÃO DE RISCO TOTAL: {resultado.pontuacao}")
        print(f"PROBABILIDADE DE SUCESSO: {resultado.probabilidade_sucesso}")
        # AGORA USA A CLASSIFICAÇÃO JÁ CALCULADA E FORMATADA PELO RiskCalculator
        print(f"CLASSIFICAÇÃO DE RISCO: {resultado.classificacao}")

        if resultado.veto_agronomico: print(f"- {resultado.veto_agronomico}")
        if resultado.pontos_atencao:
            print("\n--- PONTOS DE ATENÇÃO, RISCO E BÔNUS ---")
            for ponto in resultado.pontos_atencao: print(f"- {ponto}")
        else: print("\n- Nenhuma não-conformidade grave detectada. Plantio ideal.")
        print(self._formatar_tabela_classificacao())
        return nova_cultura

    # --- Métodos do menu ---

    def _adicionar_plantacao(self):
        print("\n--- Adicionar Nova Plantação ---")
        print("\nATENÇÃO - Diretrizes Técnicas para Cana-de-Açúcar:")
        print("Comprimento Ideal: 500m a 700m. Largura Ideal: L / 2.")
        print("Topografia Ideal: Plano/Levemente Inclinado.")
        print("Espaçamento de Ruas Ideal: 1,5m a 1,8m.")
        print("Mudas (Tolete): Mínimo de 12 gemas viáveis por metro de sulco.")
        print("Mudas (MPB): Distância Ideal entre plantas de 0,5m a 1,0m.")
        print("-" * 40)
        nova_cultura = self._selecionar_cultura_para_criar()
        if nova_cultura:
            self._service.adicionar(nova_cultura)

    def _listar_plantacoes(self):
        plantacoes = self._service.listar_todos()
        if not plantacoes:
            print("\n> Nenhuma plantação cadastrada.")
            return
        print("\n--- Lista de Plantações ---")
        for i, cultura in enumerate(plantacoes):
            print(f"Índice {i + 1}: {cultura}")

    def _selecionar_indice(self) -> Optional[int]:
        plantacoes = self._service.listar_todos()
        if not plantacoes:
            print("\n> Nenhuma plantação cadastrada para selecionar.")
            return None
        self._listar_plantacoes()
        try:
            indice = int(input("\nDigite o índice desejado: "))
            if 1 <= indice <= len(plantacoes): return indice
            else:
                print("> Índice inválido.")
                return None
        except ValueError:
            print("> Entrada inválida. Digite um número inteiro.")
            return None

    def _atualizar_plantacao(self):
        print("\n--- Atualizar Plantação ---")
        indice = self._selecionar_indice()
        if indice is not None:
            cultura_antiga = self._service.obter_por_indice(indice)
            if not cultura_antiga:
                print("> Plantação não encontrada.")
                return
            id_original = cultura_antiga.id
            data_original = cultura_antiga.data

            print(f"\nAtualizando dados para o índice {indice}. Por favor, insira os novos valores.")
            cultura_atualizada = self._selecionar_cultura_para_criar(indice_atual=indice)
            
            if cultura_atualizada:
                cultura_atualizada.id = id_original
                cultura_atualizada.data = data_original

                # Recalcula risco (opcional, pois já foi calculado dentro de _selecionar_cultura_para_criar)
                # Mas garantimos que o objeto tenha os atributos de risco preenchidos
                if not cultura_atualizada.pontuacao_risco:
                    resultado = RiskCalculator.calcular(cultura_atualizada)
                    cultura_atualizada.pontuacao_risco = resultado.pontuacao
                    cultura_atualizada.classificacao_risco = resultado.classificacao
                    cultura_atualizada.probabilidade_sucesso = resultado.probabilidade_sucesso
                    cultura_atualizada.pontos_atencao = resultado.pontos_atencao
                    cultura_atualizada.veto_agronomico = resultado.veto_agronomico

                if self._service.atualizar(cultura_atualizada):
                    print(f"\n> Plantação no índice {indice} atualizada com sucesso localmente e na nuvem (se conectado)!")
                else:
                    print("\n> Falha ao atualizar plantação.")

    def _deletar_plantacao(self):
        print("\n--- Deletar Plantação ---")
        indice = self._selecionar_indice()
        if indice is not None:
            self._service.remover_por_indice(indice)

    def _salvar_dados_json(self):
        if self._service.salvar_json():
            print("\n> Dados salvos com sucesso!")
        else:
            print("\n> Falha ao salvar dados.")

    def _conectar_oracle(self):
        print("\n--- Tentativa de Conexão Manual ---")
        solicitar_e_conectar_oracle(self._service)

    def _sair(self):
        print("\n--- Finalizando Aplicação ---")
        if input("Deseja salvar as alterações em JSON antes de sair (S/N)? ").lower() in ['s', 'sim']:
            self._service.salvar_json()
        self._service.desconectar_oracle()
        print('''\n
╭━━━┳╮╱╱╱╱╱╱╱╱╱╱╱╱╭╮╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╭━━━╮╱╱╱╱╱╱╱╱╱╱╱╭╮╱╱╱╭━━╮╱╱╱╱╱╱╱╭━━━╮╱╱╱╱╱╱╱╱╱╱╱╭╮╭╮
┃╭━╮┃┃╱╱╱╱╱╱╱╱╱╱╱╱┃┃╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱┃╭━╮┃╱╱╱╱╱╱╱╱╱╱╱┃┃╱╱╱┃╭╮┃╱╱╱╱╱╱╱┃╭━╮┃╱╱╱╱╱╱╱╱╱╱╱┃┣╯╰╮
┃┃╱┃┃╰━┳━┳┳━━┳━━┳━╯┣━━╮╭━━┳━━┳━╮╭╮╭┳━━┳━━┳━╮╭━━╮┃┃╱╰╋━━┳━╮╭━━╮╭━╯┣━━╮┃╰╯╰┳━━┳━━╮┃┃╱╰╋━━┳━╮╭━━┳╮╭┫┣╮╭╋━━┳━┳┳━━╮
┃┃╱┃┃╭╮┃╭╋┫╭╮┃╭╮┃╭╮┃╭╮┃┃╭╮┃╭╮┃╭╯┃┃┃┃━━┫╭╮┃╭╯┃╭╮┃┃┃╱╭┫╭╮┃╭╮┫╭╮┃┃╭╮┃╭╮┃┃╭━╮┃╭╮┃╭╮┃┃┃╱╭┫╭╮┃╭╮┫━━┫┃┃┃┃┃┃┃╭╮┃╭╋┫╭╮┃
┃╰━╯┃╰╯┃┃┃┃╰╯┃╭╮┃╰╯┃╰╯┃┃╰╯┃╰╯┃┃╱┃╰╯┣━━┃╭╮┃┃╱┃╭╮┃┃╰━╯┃╭╮┃┃┃┃╭╮┃┃╰╯┃╭╮┃┃╰━╯┃╰╯┃╭╮┃┃╰━╯┃╰╯┃┃┃┣━━┃╰╯┃╰┫╰┫╰╯┃┃┃┃╭╮┣╮
╰━━━┻━━┻╯╰┻━╮┣╯╰┻━━┻━━╯┃╭━┻━━┻╯╱╰━━┻━━┻╯╰┻╯╱╰╯╰╯╰━━━┻╯╰┻╯╰┻╯╰╯╰━━┻╯╰╯╰━━━┻━━┻╯╰╯╰━━━┻━━┻╯╰┻━━┻━━┻━┻━┻━━┻╯╰┻╯╰┻╯
╱╱╱╱╱╱╱╱╱╱╭━╯┃╱╱╱╱╱╱╱╱╱┃┃
╱╱╱╱╱╱╱╱╱╱╰━━╯╱╱╱╱╱╱╱╱╱╰╯
╭━━━╮╭╮╱╱╱╱╱╱╱╱╱╱╱╱╱╱╭╮
┃╭━╮┣╯╰╮╱╱╱╱╱╱╱╱╱╱╱╱╱┃┃
┃┃╱┃┣╮╭╋━━╮╭╮╭┳━━┳┳━━┫┃
┃╰━╯┃┃┃┃┃━┫┃╰╯┃╭╮┣┫━━╋╯
┃╭━╮┃┃╰┫┃━┫┃┃┃┃╭╮┃┣━━┣╮
╰╯╱╰╯╰━┻━━╯╰┻┻┻╯╰┻┻━━┻╯
\n
''')
        return True

    def exibir(self):
        deve_sair = False
        while not deve_sair:
            print('''
                  
╭━━━╮╱╱╱╱╱╱╱╱╱╱╱╭╮╱╱╱╭━━╮
┃╭━╮┃╱╱╱╱╱╱╱╱╱╱╱┃┃╱╱╱┃╭╮┃
┃┃╱╰╋━━┳━╮╭━━╮╭━╯┣━━╮┃╰╯╰┳━━┳━━╮
┃┃╱╭┫╭╮┃╭╮┫╭╮┃┃╭╮┃╭╮┃┃╭━╮┃╭╮┃╭╮┃
┃╰━╯┃╭╮┃┃┃┃╭╮┃┃╰╯┃╭╮┃┃╰━╯┃╰╯┃╭╮┃
╰━━━┻╯╰┻╯╰┻╯╰╯╰━━┻╯╰╯╰━━━┻━━┻╯╰╯\n
''')
            for key, (label, _) in self._opcoes.items():
                print(f"{key}. {label}")
            escolha = input("Escolha uma opção: ")
            opcao = self._opcoes.get(escolha)
            if opcao:
                resultado = opcao[1]()
                if resultado is True: deve_sair = True
            else: print("\n> Opção inválida. Tente novamente.")