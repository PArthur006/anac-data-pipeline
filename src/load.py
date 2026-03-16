import os 
import logging
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path

# 1. Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 2. Configuração de Caminhos
BASE_DIR = Path(__file__).resolve().parent.parent
SILVER_DIR = BASE_DIR / "data" / "silver" / "vra_condolidado"

def construir_string_conexao():
    """Lê as credenciais do .env de forma segura."""
    load_dotenv()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db = os.getenv("DB_NAME")

    if not all ([user, password, host, port, db]):
        logger.critical("Variáveis de ambiente ausentes. Verifique o arquivo .env.")
        raise ValueError("Credenciais de banco de dados imcompletas.")
    
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

def modelar_e_carregar_dados():
    logger.info("Iniciando carga analítica (Camada Gold)...")

    # Valida se a camada Silver existe
    if not SILVER_DIR.exists():
        raise FileNotFoundError(f"Camada Silver não encontrada em {SILVER_DIR}")

    # Lê o dataset particionado inteiro
    logger.info("Lendo base Parquet particionada da Camada Silver...")
    df_silver = pd.read_parquet(SILVER_DIR)
    logger.info(f"Total de registros na memória: {len(df_silver)}")

    # ===================================
    # MODELAGEM DIMENSIONAL (STAR SCHEMA)
    # ===================================

    # 1. Dimensão Empresa
    logger.info("Modelando Dimensão: Empresa...")
    dim_empresa = df_silver[['empresa_sigla', 'empresa_nome', 'empresa_nacionalidade']].copy()
    dim_empresa = dim_empresa.dropna(subset=['empresa_sigla'])
    dim_empresa = dim_empresa.drop_duplicates(subset=['empresa_sigla']).reset_index(drop=True)

    # 2. Dimensão Aeroporto (Unificando Origem e Destino)
    logger.info("Modelando Dimensão: Aeroporto...")
    aero_origem = df_silver[[
        'aeroporto_de_origem_sigla', 'aeroporto_de_origem_nome', 'aeroporto_de_origem_uf', 'aeroporto_de_origem_regiao', 'aeroporto_de_origem_pais', 'aeroporto_de_origem_continente'
    ]].copy()
    aero_origem.columns = ['sigla', 'nome', 'uf', 'regiao', 'pais', 'continente']

    aero_destino = df_silver[[
        'aeroporto_de_destino_sigla', 'aeroporto_de_destino_nome', 'aeroporto_de_destino_uf', 'aeroporto_de_destino_regiao', 'aeroporto_de_destino_pais', 'aeroporto_de_destino_continente'
    ]].copy()
    aero_destino.columns = ['sigla', 'nome', 'uf', 'regiao', 'pais', 'continente']

    # Empilha, remove nulos na PK e remove duplicatas
    dim_aeroporto = pd.concat([aero_origem, aero_destino], ignore_index=True)
    dim_aeroporto = dim_aeroporto.dropna(subset=['sigla'])
    dim_aeroporto = dim_aeroporto.drop_duplicates(subset=['sigla']).reset_index(drop=True)

    # 3. Tabela Fato
    logger.info("Modelando Tabela Fato: Voos Mensais...")
    colunas_fato = [
        'ano', 'mes', 'empresa_sigla', 'aeroporto_de_origem_sigla', 'aeroporto_de_destino_sigla',
        'natureza', 'grupo_de_voo', 'passageiros_pagos', 'passageiros_gratis', 'carga_paga_kg',
        'carga_gratis_kg', 'correio_kg', 'ask', 'rpk', 'atk', 'rtk', 'combustivel_litros',
        'distancia_voada_km', 'decolagens', 'carga_paga_km', 'carga_gratis_km', 'correio_km',
        'assentos', 'payload', 'horas_voadas', 'bagagem_kg'
    ]
    fato_voo = df_silver[colunas_fato].copy()

    # Remove registros que não tem chaves estrangeiras válidas
    fato_voo = fato_voo.dropna(subset=['empresa_sigla', 'aeroporto_de_origem_sigla', 'aeroporto_de_destino_sigla'])

    # ===================================
    # CARGA NO BANCO DE DADOS
    # ===================================
    
    logger.info("Estabelecendo conexão com o PostgreSQL...")
    engine = create_engine(construir_string_conexao())

    try:
        # Inserção em chunks para não estourar a memória RAM e o buffer do banco.
        logger.info(f"Caregando dim_empresa ({len(dim_empresa)} registros)...")
        dim_empresa.to_sql('dim_empresa', engine, if_exists='replace', index=False, chunksize=10000)

        logger.info(f"Carregando dim_aeroporto ({len(dim_aeroporto)} registros)...")
        dim_aeroporto.to_sql('dim_aeroporto', engine, if_exists='replace', index=False, chunksize=10000)

        logger.info(f"Carregando fato_voo_mensal ({len(fato_voo)} registros)...")
        fato_voo.to_sql('fato_voo_mensal', engine, if_exists='replace', index=False, chunksize=50000)

        logger.info("Pipeline concluído com sucesso! Os dados estão na Camada Gold.")

    except Exception as e:
        logger.error(f"Erro durante a inserção no banco de dados: {e}")
        raise

if __name__ == "__main__":
    modelar_e_carregar_dados()