# ANAC Data Pipeline: Análise de Tráfego Aéreo Brasileiro

Pipeline de dados analitico e escalável construído para processar, modelar e visualizar mais de duas décadas de operações aéreas no Brasil (2000-2020), utilizando dados abertos da Agência Nacional de Aviação Civil (ANAC).

## Objetivo do Projeto

Demonstrar a construção de uma arquitetura de dados moderna ponta a ponta. O projeto eleva dados brutos e desestruturados a um Data Warehouse modelado para *Business Intelligence*, garantindo alta performance de consulta, governança de dados e resiliência de infraestrutura.

## Inteligência de Negócio (Business Value)

Diferente de painéis de contagem absoluta, a Camada Gold deste projeto foi desenhada para extrair métricas reais da indústria da aviação.

- **Taxa de Ocupação Global (Load Factor):** Cálculo exato entre RPK (Demanda) e ASK (Oferta).
- **Dinâmica de Market Share:** Histórico visual do monopólio do setor, ascensão e falência das top 6 companhia aéreas brasileiras.
- **Eficiência Operacional de Frota:** Mapeamento de gargalos e densidade através da média de passageiros reais alocados por decolagem nas rotas mais movimentadas do país.

## Arquitetura e Tecnologias

O projeto adota a **Arquitetura Medallion** (Bronze, Silver, Gold), garantindo qualidade e rastreabilidade dos dados:

- **Camada Bronze (Raw):** Extração de dumps CSV brutos do portal da ANAC.
- **Camada Silver (Cleansed):** Processamento distribuído com **Apache Spark (PySpark)**, padronização de nomenclatura (snake_case), tipagem de colunas e armazenamento em **Parquet** particionado por *`ano`*.
- **Camada Gold (Analytics):** Modelagem dimensional (**Star Schema**) com **Pandas e SQLAlchemy**, gerando *`fato_voo_mensal`*, *`dim_aeroporto`* e *`dim_empresa`* em **PostgreSQL**.
- **Visualização:** Dashboard interativo em **Streamlit e Plotly**, com cache em memória para resposta em milissegundos e processamento de estado via Pandas.

## Resiliência e Graceful Degradation

A aplicação visual possui um mecanismo de tolerância e falhas (*fallback*) embutido para garantir alta disponibilidade:

1. **Rota de Produção:** Se as variáveis de ambiente existirem, o SQLAlchemy roteia as queries para o servidor **PostgreSQL**.
2. **Rota de Fallback:** Na ausência da infraestrutura (ex: deploy em nuvem sem secrets configurados), o sistema mapeia a conexão automaticamente para um banco **SQLite** local e embarcado (*data/anac_gold.db*), degradando graciosamente sem derrubar a aplicação.

## Como Executar Localmente

### Pré-requisitos

- Python 3.9+
- PostgreSQL (opcional para rota de produção)
- Java/Hadoop Winutils (para execução do PySpark no Windows)

### 1) Clonar o repositório

```bash
git clone https://github.com/PArthur006/anac-data-pipeline.git
cd anac-data-pipeline
```

### 2) Criar e ativar ambiente virtual

```bash
python -m venv venv
```

Linux/macOS:

```bash
source venv/bin/activate
```

Windows (PowerShell):

```powershell
venv\Scripts\Activate.ps1
```

### 3) Instalar dependências

```bash
pip install -r requirements.txt
```

### 4) Configurar variáveis de ambiente (opcional para PostgreSQL)

Copie `.env.example` para `.env` e ajuste os valores conforme seu ambiente.

```bash
cp .env.example .env
```

No Windows, você também pode criar/editar manualmente o arquivo `.env`.

## Fluxo Completo do Pipeline

### Etapa A: Bronze (extração)

```bash
python src/extract.py
```

Saída esperada: `data/bronze/dados_estatisticos.csv`

### Etapa B: Silver (transformação com Spark)

```bash
python src/transform.py
```

Saída esperada: `data/silver/vra_condolidado/` em Parquet, particionado por `ano`.

### Etapa C: Gold (carga analítica no PostgreSQL)

```bash
python src/load.py
```

Tabelas geradas:

- `dim_empresa`
- `dim_aeroporto`
- `fato_voo_mensal`

### Etapa D: Exportar fallback para SQLite (opcional, recomendado para deploy local/cloud)

```bash
python src/export_sqlite.py
```

Saida esperada: `data/anac_gold.db`

### Etapa E: Executar dashboard

```bash
streamlit run app/dashboard.py
```

### Observações:

- Com `.env` válido, o dashboard usa PostgreSQL.
- Sem `.env` (ou sem infraestrutura), o dashboard usa SQLite local (`data/anac_gold.db`).

## Estrutura de Pastas e Arquivos

Abaixo está a disposição das pastas e arquivos do projeto, organizada para refletir as diferentes etapas do pipeline de dados:

```
anac-data-pipeline/
├── README.md                # Documentação técnica e arquitetural
├── requirements.txt         # Dependências diretas do projeto
├── app/                     # Camada de Apresentação
│   ├── dashboard.py         # Interface visual (Streamlit)
│   ├── queries.py           # Motor de extração SQL e lógicas Pandas
├── data/                    # Data Lake Local
│   ├── bronze/              # Landing zone (CSV)
│   ├── silver/              # Cleansed zone (Parquet particionado)
│   │   └── vra_consolidado/
│   │       ├── _SUCCESS
│   │       ├── ano=2000/
│   │       └── ...
│   └── anac_gold.db         # Banco embarcado de Fallback (SQLite)
├── notebooks/               # Ambiente de exploração e prototipagem
│   └── 01_exploracao_bronze.ipynb
├── src/                     # Motor de ETL / ELT
│   ├── extract.py           # Ingestão de dados
│   ├── transform.py         # Processamento com PySpark
│   ├── load.py              # Carga no Data Warehouse
│   └── export_sqlite.py     # Geração do banco de contingência
```

Essa estrutura foi projetada para separar claramente as responsabilidades de cada componente do pipeline, facilitando a manutenção e escalabilidade.