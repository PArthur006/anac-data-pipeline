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

# Função de extração com Cache: Evita bater no banco de dados a cada interação do usuário.
@st.cache_data(ttl=3600) 
def obter_kpis_gerais():
    engine = get_database_connection()
    query = """
        SELECT
            SUM(passageiros_pagos) as total_passageiros,
            SUM(decolagens) as total_decolagens,
            SUM(carga_paga_kg) / 1000 as total_carga_toneladas
        FROM fato_voo_mensal
    """
    return pd.read_sql(query, engine)

@st.cache_data(ttl=3600)
def obter_evolucao_voos_por_ano():
    engine = get_database_connection()
    query = """
        SELECT
            ano,
            SUM(decolagens) as total_voos
        FROM fato_voo_mensal
        WHERE CAST(ano AS INTEGER) < 2021
        GROUP BY ano
        ORDER BY ano
    """
    
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

@st.cache_data(ttl=3600)
def obter_top_aeroportos(limite=10):
    engine = get_database_connection()
    query = text("""
        SELECT
            da.nome as aeroporto,
            CAST(SUM(f.passageiros_pagos) AS FLOAT) as volume_passageiros
        FROM fato_voo_mensal f
        JOIN dim_aeroporto da ON f.aeroporto_de_origem_sigla = da.sigla
        WHERE f.passageiros_pagos IS NOT NULL and f.passageiros_pagos > 0
        GROUP BY da.nome
        ORDER BY volume_passageiros DESC NULLS LAST
        LIMIT :limite
    """)

    # Conexão explícita gerenciada
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"limite": limite})
