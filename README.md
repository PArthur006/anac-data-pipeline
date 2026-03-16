# ANAC Data Pipeline: Analise de Trafego Aereo Brasileiro

Pipeline de dados analitico construído para processar, modelar e visualizar mais de duas décadas de operações aéreas no Brasil (2000-2020), utilizando dados abertos da Agência Nacional de Aviação Civil (ANAC).

## Objetivo do Projeto

Demonstrar a construção de uma arquitetura de dados moderna ponta a ponta, saindo de dados brutos e desestruturados para um Data Warehouse modelado para Business Intelligence, com performance e resiliência.

## Arquitetura e Tecnologias

O projeto adota a Arquitetura Medallion (Bronze, Silver, Gold), garantindo qualidade e rastreabilidade dos dados:

- Camada Bronze (Raw): extração de dumps CSV brutos do portal da ANAC.
- Camada Silver (Cleansed): processamento distribuído com Apache Spark (PySpark), padronização de nomenclatura (snake_case), tipagem de colunas e armazenamento em Parquet particionado por `ano`.
- Camada Gold (Analytics): modelagem dimensional (Star Schema) com Pandas e SQLAlchemy, gerando `fato_voo_mensal`, `dim_aeroporto` e `dim_empresa` em PostgreSQL.
- Apresentacao: dashboard interativo em Streamlit + Plotly, com cache em memória para consultas analíticas.

## Resiliência e Graceful Degradation

A aplicação visual foi projetada com fallback automático:

1. Rota de Produção: se as variáveis de ambiente estiverem presentes, conecta ao PostgreSQL.
2. Rota de Fallback: na ausência da infraestrutura principal, conecta ao SQLite local (`data/anac_gold.db`).

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