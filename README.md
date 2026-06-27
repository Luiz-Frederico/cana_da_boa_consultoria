# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
  <a href="https://www.fiap.com.br/">
    <img src="https://github.com/Luiz-Frederico/templateFiap/blob/main/assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width="40%" height="40%">
  </a>
</p>

<br>

---

# 🌾 CANA DA BOA CONSULTORIA

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Oracle](https://img.shields.io/badge/Oracle_Database-19c%2F21c-F80000?style=for-the-badge&logo=oracle&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Hexagonal_Clean-blue?style=for-the-badge)
![Security](https://img.shields.io/badge/Security-Env_Vars%2BBind_Variables-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey?style=for-the-badge)

---

## 📋 Integrantes

<table>
  <tr>
    <td width="150" align="center" valign="top">
      <a href="https://github.com/Luiz-Frederico">
        <img src="https://github.com/Luiz-Frederico.png" width="100" height="100" alt="Luiz Campelo" style="border-radius:50%; object-fit:cover;" />
      </a>
      <br/><strong>Luiz Campelo</strong><br/>
      <a href="https://github.com/Luiz-Frederico">@Luiz-Frederico</a>
    </td>
  </tr>
</table>

---

## 👩‍🏫 Professores e Orientadores

### 🧭 Coordenador(a)

<table>
  <tr>
    <td width="150" align="center" valign="top">
      <a href="https://github.com/agodoi">
        <img src="https://github.com/agodoi.png" width="100" height="100" alt="André Godoi" style="border-radius:50%; object-fit:cover;" />
      </a>
      <br/><strong>André Godoi</strong><br/>
      <span>Coordenador(a)</span><br/>
      <a href="https://github.com/agodoi">@agodoi</a>
    </td>
  </tr>
</table>

### 👩‍🏫 Tutor(a)

<table>
  <tr>
    <td width="150" align="center" valign="top">
      <a href="https://github.com/SabrinaOtoni">
        <img src="https://github.com/SabrinaOtoni.png" width="100" height="100" alt="Sabrina Otoni" style="border-radius:50%; object-fit:cover;" />
      </a>
      <br/><strong>Sabrina Otoni</strong><br/>
      <span>Tutor(a)</span><br/>
      <a href="https://github.com/SabrinaOtoni">@SabrinaOtoni</a>
    </td>
  </tr>
</table>

---

## 📜 Descrição do Projeto

**Cana da Boa Consultoria** é uma aplicação de engenharia de software desenvolvida para o gerenciamento de dados operacionais e análise preditiva de riscos agronômicos no cultivo da cana-de-açúcar. O sistema automatiza a avaliação de variáveis críticas de manejo — dimensões do talhão, topografia, conformidade do espaçamento entre ruas, janelas climáticas de plantio e fatores operacionais —, oferecendo diagnósticos preditivos sobre a viabilidade operacional e a probabilidade de sucesso de cada plantação.

### 🎯 Propósito

O projeto nasceu como um exercício acadêmico na **FIAP**, mas foi elevado a um nível de **solução profissional** ao incorporar padrões de arquitetura de software, segurança da informação e integração com banco de dados corporativo. A aplicação é um exemplo prático de como unir:

- **Regras de negócio complexas** do setor sucroenergético.
- **Arquitetura de software modular** com separação de responsabilidades.
- **Persistência híbrida** (JSON local + Oracle Cloud) com sincronização em tempo real.
- **Segurança** no tratamento de credenciais e prevenção contra SQL Injection.
- **Usabilidade** em interface de console com feedbacks de ricos e validações interativas.

---

## 🏛️ Arquitetura da Solução

### 🔹 Visão Geral

A aplicação segue uma arquitetura **Hexagonal / Clean Architecture**, com camadas bem definidas e desacopladas:

```

┌─────────────────────────────────────────────────────────────────────┐
│                         UI / Console Menu                           │
│  (Interação com o usuário, coleta de dados, exibição de feedbacks)  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Service Layer                               │
│        (Orquestração, regras de negócio, validações)                │
│                    PlantacaoService                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌──────────────────┐   ┌──────────────────────────┐   ┌──────────────────┐
│   Domain Layer   │   │    Persistence Layer     │   │   Utils Layer    │
│                  │   │                          │   │                  │
│ • Models (Cana)  │   │ • JsonRepository         │   │ • Sanitizer      │
│ • RiskCalculator │   │ • OracleRepository       │   │ • Logger         │
│ • DTOs           │   │ • Base (Interface)       │   │ • Classificação  │
└──────────────────┘   └──────────────────────────┘   └──────────────────┘

```

### 🔹 Camadas e Responsabilidades

| Camada | Responsabilidade |
|--------|------------------|
| **UI (Console)** | Interface com o usuário: coleta de dados, validações de entrada, exibição de feedbacks e relatórios. |
| **Service** | Orquestração das operações: coordena os repositórios, aplica validações de unicidade e gerencia o estado da aplicação. |
| **Domain** | Lógica de negócio agronômica: regras de cálculo de risco, modelos de dados (Cana, Planta, DetalhesPlantio) e DTOs para transporte de resultados. |
| **Repositories** | Persistência de dados: `JsonRepository` (armazenamento local) e `OracleRepository` (sincronização com banco de dados Oracle). Ambos implementam a interface `PlantacaoRepository`. |
| **Utils** | Funções auxiliares: sanitização de strings, normalização de textos, logging e classificação de risco. |

### 🔹 Padrões de Projeto Aplicados

| Padrão | Aplicação |
|--------|-----------|
| **Repository** | Abstração da persistência. Permite trocar a fonte de dados (JSON ↔ Oracle) sem alterar a lógica de negócio. |
| **Service Layer** | Orquestração das operações, separando a lógica de negócio da interface e da persistência. |
| **Data Transfer Object (DTO)** | `RiscoResultado` encapsula o resultado do cálculo de risco, isolando o domínio da UI. |
| **Dependency Inversion (DIP)** | O `PlantacaoService` depende da abstração `PlantacaoRepository`, não das implementações concretas. |
| **Factory / Static Factory** | `Cana.from_dict()` e `Cana.to_dict()` para conversão entre objetos e dicionários. |
| **Strategy** | `RiskCalculator` encapsula a lógica de cálculo de risco, permitindo futuras variações. |

---

## 🔐 Segurança e Boas Práticas
### 🔹 Credenciais e Configurações

O sistema utiliza **variáveis de ambiente** através do arquivo `.env` para armazenar credenciais sensíveis, eliminando a exposição de senhas e usuários no código-fonte.

```env
ORACLE_USER=system
ORACLE_PASSWORD=sua_senha_aqui
ORACLE_DSN=localhost:1521/xe

```

### 🔹 Prevenção contra SQL Injection
Todas as interações com o banco de dados Oracle utilizam Bind Variables (parâmetros nomeados), garantindo que os dados do usuário sejam tratados como valores, não como código executável.
```
cursor.execute(sql_merge, {
    "id": cultura.id,
    "prop": cultura.propriedade,
    "dt": cultura.data,
    "talhao": cultura.talhao,
    "risco": risco_limpo,
    "json_data": json_payload
})
```
### 🔹 Sanitização de Dados
Todas as entradas de texto passam por um processo de sanitização centralizado (```utils/sanitizer.py```), removendo acentos, caracteres especiais e formatações que possam causar inconsistências no banco de dados ou no JSON.

### 🔹 Logs de Auditoria
Operações críticas (```inserções, atualizações, exclusões, sincronizações```) são registradas no arquivo registro_operacoes.log, permitindo rastreabilidade e auditoria.

### 🔹 Resiliência de Rede
O OracleRepository implementa um mecanismo de reconexão automática em caso de falha de comunicação (```DPY-4011```), garantindo que operações sejam concluídas mesmo com instabilidade de rede.

---

## 📂 Estrutura de Pastas do Repositório

```text
cana_da_boa_consultoria/
├── .env                              # Credenciais do Oracle (não versionado)
├── .gitignore                        # Arquivos ignorados pelo Git
├── README.md                         # Documentação principal
├── requirements.txt                  # Dependências do projeto
├── main.py                           # Ponto de entrada da aplicação
│
├── config/                           # Configurações globais
│   ├── __init__.py
│   └── settings.py                   # Carrega .env e constantes do sistema
│
├── database/                         # Camada de infraestrutura (legado)
│   ├── __init__.py
│   ├── oracle_connection.py          # Versão original (mantida para referência)
│   └── schema.sql                    # DDL de criação da tabela no Oracle
│
├── domain/                           # Camada de domínio e regras de negócio
│   ├── __init__.py
│   ├── dtos.py                       # Data Transfer Objects (RiscoResultado)
│   ├── models.py                     # Entidades: Cana, Planta, DetalhesPlantio, Insumo
│   └── risk_calculator.py            # Motor de cálculo de risco agronômico
│
├── repositories/                     # Camada de persistência (nova arquitetura)
│   ├── __init__.py
│   ├── base.py                       # Interface PlantacaoRepository (ABC)
│   ├── json_repository.py            # Repositório JSON (armazenamento local)
│   └── oracle_repository.py          # Repositório Oracle (sincronização em batch)
│
├── services/                         # Camada de orquestração
│   ├── __init__.py
│   └── plantacao_service.py          # PlantacaoService (coordena JSON + Oracle)
│
├── ui/                               # Interface com o usuário (console)
│   ├── __init__.py
│   └── console_menu.py               # Menu interativo e fluxos de navegação
│
└── utils/                            # Utilitários e funções auxiliares
    ├── __init__.py
    ├── classificacao.py              # Classificação de risco por probabilidade
    ├── helpers.py                    # Logging e funções gerais
    └── sanitizer.py                  # Sanitização de strings e payloads
```
> 💡 <small>**Nota sobre Logs de Auditoria:** O arquivo de auditoria registro_operacoes.log está explicitamente mapeado no .gitignore. Por motivos de segurança e boas práticas de desenvolvimento, ele não é rastreado pelo controle de versão, sendo gerado dinamicamente de forma local pelo motor do sistema (utils/helpers.py) logo após a primeira execução da aplicação.
>


## 🗄️ Modelagem de Dados (Oracle)



#### Tabela `PLANTIO_CANA`

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| **ID** | NUMBER | Identificador único sequencial (Chave Primária) |
| **PROPRIEDADE** | VARCHAR2(150) | Nome ou código da propriedade |
| **DATA_REGISTRO** | DATE | Data de inclusão do registro |
| **TALHAO** | VARCHAR2(50) | Identificação do talhão |
| **RISCO_AGRONOMICO** | VARCHAR2(50) | Classificação final de risco |
| **DADOS_JSON** | CLOB | Metadados operacionais em formato JSON |
---

## 🔹 Consultas Analíticas com JSON
A coluna DADOS_JSON permite consultas diretas com JSON_VALUE, possibilitando mineração de dados nativa no Oracle:

```
SELECT p.PROPRIEDADE, 
       JSON_VALUE(p.DADOS_JSON, '$.detalhes_plantio.metodo') AS METODO_PLANTIO,
       JSON_VALUE(p.DADOS_JSON, '$.probabilidade_sucesso') AS CHANCE_SUCESSO
FROM PLANTIO_CANA p
WHERE JSON_VALUE(p.DADOS_JSON, '$.classificacao_risco') = 'RISCO BAIXO';

```

## ⚙️ Principais Funcionalidades

### 🔹 CRUD Completo com Sincronização Híbrida
Adicionar Plantação: Coleta de dados via console, cálculo de risco e persistência local em JSON.

Listar Plantações: Exibe todas as plantações cadastradas com seus detalhes e classificação de risco.

Atualizar Plantação: Permite editar uma plantação existente, recalculando o risco e sincronizando com o Oracle.

Deletar Plantação: Remove uma plantação do JSON local e do Oracle (se conectado).

Salvar Dados: Força a persistência dos dados em JSON.

Conectar Oracle: Estabelece conexão com o banco de dados e sincroniza registros em lote.

### 🔹 Cálculo de Risco Agronômico
O motor de regras avalia a viabilidade operacional cruzando os dados de entrada com parâmetros normativos do setor:

Dimensões do Talhão: Classifica a eficiência de manobra de maquinários com base no comprimento e largura.

Espaçamento entre Ruas: Valida a compatibilidade com a colheita mecanizada padrão.

Janela de Época de Plantio: Confronta o mês escolhido com os regimes hídricos de produção.

Matriz de Riscos Operacionais: Consolida um score de risco incremental baseado em boas práticas de manejo (irrigação, preparo de solo, controle de tráfego, piloto automático, variedades, mão de obra e velocidade de colheita).

Veto Topográfico: Topografia acidentada não pode ser compensada por bônus de manejo.

### 🔹 Tabela de Classificação de Risco

| Pontuação | Probabilidade Esperada | Classificação |
| :---: | :---: | :--- |
| **0** | 96% - 99% | RISCO MINIMO |
| **1 a 2** | 86% - 95% | RISCO MUITO BAIXO |
| **3 a 5** | 76% - 85% | RISCO BAIXO |
| **6 a 8** | 67% - 75% | RISCO MEDIO/BAIXO |
| **9 a 12** | 51% - 66% | RISCO MEDIO |
| **13 a 18** | 31% - 50% | RISCO ALTO |
| **> 18** | 0% - 30% | RISCO ALTISSIMO |
---

## 🚀 Manual de Execução

### Pré-requisitos
* **Python 3.10** ou superior instalado.
* **Oracle Database** (local ou cloud) com credenciais de acesso.
* **Git** para clonar o repositório.

### Passo a Passo

1. **Clone o repositório:**
  
   ```bash
   git clone git@github.com:Luiz-Frederico/cana_da_boa_consultoria.git

2. **Navegue até o diretório do projeto:**
   ```bash
   cd cana_da_boa_consultoria

3. **Crie um ambiente virtual (recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
        ou
   venv\Scripts\activate     # Windows
  
4. **Instale as dependências obrigatórias:**
   ```bash
   pip install -r requirements.txt

5. **Configure as credenciais do Oracle -**
Crie um arquivo ```.env``` na raiz do projeto com:
    ```bash
    ORACLE_USER=seu_usuario
    ORACLE_PASSWORD=sua_senha
    ORACLE_DSN=localhost:1521/xe
    
7. **Execute a aplicação:**
   ```bash
   python main.py

## 🔹 Primeira Execução
Ao iniciar o aplicativo, você será perguntado se deseja conectar ao Oracle. Se optar por conectar:

O sistema validará a existência da tabela PLANTIO_CANA e a criará automaticamente, se necessário.

Uma sequência (SEQ_PLANTIO_CANA) será criada para gerenciamento de IDs.

Você poderá sincronizar todos os dados locais (JSON) com o Oracle em lote (executemany).

Novos cadastros serão espelhados automaticamente em tempo real na nuvem.   

---

## 🧪 Exemplo de Uso
Adicionando uma Nova Plantação
No menu principal, selecione 1. Adicionar Plantação.

Siga as instruções para informar:

Propriedade e talhão.

Tipo de terreno (plano, levemente inclinado, acidentado).

Espaçamento entre ruas (em metros).

Método de plantio (Toletes ou MPB).

Dimensões do terreno (comprimento e largura).

Fatores de manejo (irrigação, preparo do solo, controle de pragas, etc.).

O sistema calculará automaticamente a pontuação de risco, a probabilidade de sucesso e a classificação.

Os dados serão salvos localmente em plantacoes_data.json e, se o Oracle estiver conectado, sincronizados em tempo real.

Visualizando o Relatório de Risco
Após adicionar uma plantação, o console exibe um resumo detalhado com:

Classificações individuais (topografia, espaçamento, método, época, dimensões).

Fatores de manejo (com indicação de bônus ou riscos).

Pontuação final, probabilidade de sucesso e classificação consolidada.

Pontos de atenção e vetos agronômicos (se houver).

---

### 🤖 Tecnologias e Ferramentas

| Tecnologia | Versão | Finalidade |
| :--- | :---: | :--- |
| **Python** | 3.10+ | Linguagem de desenvolvimento |
| **Oracle Database** | 19c / 21c | Banco de dados relacional com suporte a JSON |
| **python-oracledb** | 2.0+ | Driver oficial da Oracle para Python |
| **python-dotenv** | 1.0+ | Gerenciamento de variáveis de ambiente |
| **Git** | - | Controle de versão |
| **GitHub** | - | Hospedagem do repositório |

---

## 📌 Princípios de Engenharia de Software Aplicados

### 🔹 SOLID
Single Responsibility: Cada classe tem uma única responsabilidade (UI, Service, Repository, Domain).

Open/Closed: Novos repositórios podem ser adicionados sem modificar o Service (via interface PlantacaoRepository).

Liskov Substitution: JsonRepository e OracleRepository podem ser usados indistintamente.

Interface Segregation: A interface PlantacaoRepository contém apenas métodos necessários.

Dependency Inversion: O Service depende da abstração, não das implementações concretas.

### 🔹 Clean Code
Nomes de variáveis, métodos e classes claros e descritivos.

Métodos curtos e focados em uma única tarefa.

Comentários explicativos quando necessário.

Código auto-documentado.

### 🔹 Segurança
Credenciais via variáveis de ambiente (.env).

Bind variables no Oracle para prevenir SQL Injection.

Sanitização de dados antes da persistência.

Logs de auditoria para rastreabilidade.

### 🔹 Performance
executemany para sincronização em lote no Oracle.

Armazenamento em JSON local para operações rápidas offline.

Cálculo de risco otimizado com lógica determinística.

---
### 🤝 Contribuição
Este projeto foi desenvolvido como parte de um exercício acadêmico na FIAP. Contribuições, sugestões e melhorias são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests no repositório oficial.

---
## 📚 Referências

* **[Python 3.10+ Documentation](https://docs.python.org/3/)** - Base de desenvolvimento e tipagem estática do projeto.
* **[python-oracledb Driver Documentation](https://oracle.github.io/python-oracledb/)** - Documentação oficial do driver Thin da Oracle utilizado para a persistência de dados.
* **[Oracle Database SQL Language Reference](https://docs.oracle.com/en/database/oracle/oracle-database/index.html)** - Padrão de sintaxe SQL, DDL, DML e uso de *Bind Variables* aplicados no projeto.
* **[Git & GitHub Documentation](https://git-scm.com/doc)** - Boas práticas de controle de versão e gerenciamento de repositórios.
* [FIAP](https://www.fiap.com.br/online/graduacao/tecnologo/inteligencia-artificial/) - Arquitetura de Software e Engenharia de Dados (Curso de Inteligência Artificial - Fase 2).

---
## 📝 Licença
Este projeto está licenciado sob a Licença Creative Commons Atribuição 4.0 Internacional. Para mais detalhes, consulte o arquivo [LICENSE](LICENSE).
  
   
