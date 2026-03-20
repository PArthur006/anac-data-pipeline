import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa a conexão com o bacno de forma otimizada (apenas uma vez).
@st.cache_resource
def get_database_connection():
    host = os.getenv("DB_HOST")
    
    if host:
        # ROTA 1: Infraestrutura Completa (PostgreSQL)
        st.sidebar.success("Conectado ao PostgreSQL (Produção/Local)")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        port = os.getenv("DB_PORT")
        db = os.getenv("DB_NAME")
        conexao = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    else:
        # ROTA 2: Fallback (SQLite Local)
        st.sidebar.warning("Conectado ao SQLite (Modo Fallback)")
        BASE_DIR = Path(__file__).resolve().parent.parent
        sqlite_path = BASE_DIR / "data" / "anac_gold.db"
        conexao = f"sqlite:///{sqlite_path}"
        
    return create_engine(conexao)

# Função para obter KPIs de negócio: Total de passageiros, carga transportada e taxa de ocupação.
@st.cache_data(ttl=3600)
def obter_kpis_negocio():
    engine = get_database_connection()
    # RPK (Demanda) / ASK (Oferta) = Taxa de Ocupação
    query = text("""
        SELECT
            SUM(passageiros_pagos) as total_passageiros,
            SUM(carga_paga_kg) / 1000 as total_carga_toneladas,
            CASE
                 WHEN SUM(ask) = 0 THEN 0
                 ELSE (SUM(rpk) / CAST(SUM(ask) AS FLOAT)) * 100
            END as load_factor
        FROM fato_voo_mensal
        WHERE CAST(ano AS INTEGER) < 2021
""")
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

# Função para obter o market share das companhias aéreas ao longo do tempo.
@st.cache_data(ttl=3600)
def obter_market_share_companhias():
    engine = get_database_connection()
    query = text("""
        SELECT
            f.ano,
            e.empresa_nome as empresa,
            SUM(f.passageiros_pagos) as passageiros
        FROM fato_voo_mensal f
        JOIN dim_empresa e ON f.empresa_sigla = e.empresa_sigla
        WHERE CAST(f.ano AS INTEGER) < 2021 AND f.passageiros_pagos IS NOT NULL
        GROUP BY f.ano, e.empresa_nome
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        
    top_empresas = df.groupby('empresa')['passageiros'].sum().nlargest(6).index
    df['empresa_agrupada'] = df['empresa'].where(df['empresa'].isin(top_empresas), 'Outras')
    df_final = df.groupby(['ano', 'empresa_agrupada'])['passageiros'].sum().reset_index()
    
    return df_final

# Função para obter a eficiência das rotas (passageiros por voo) e identificar as mais eficientes.
@st.cache_data(ttl=3600)
def obter_eficiencia_rotas(limite=10):
    engine = get_database_connection()
    query = text("""
        SELECT
            origem.nome || ' -> ' || destino.nome as rota,
            CAST(SUM(f.passageiros_pagos) AS FLOAT) / SUM(f.decolagens) as passageiros_por_voo
        FROM fato_voo_mensal f
        JOIN dim_aeroporto origem ON f.aeroporto_de_origem_sigla = origem.sigla
        JOIN dim_aeroporto destino ON f.aeroporto_de_destino_sigla = destino.sigla
        WHERE f.decolagens > 500 AND f.passageiros_pagos IS NOT NULL
        GROUP BY origem.nome, destino.nome
        ORDER BY passageiros_por_voo DESC NULLS LAST
        LIMIT :limite
""")
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"limite": limite})

