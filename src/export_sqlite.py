import os
import logging
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def exportar_para_sqlite():
    load_dotenv()
    
    # 1. Conexão Origem
    user, password, host, port, db = map(os.getenv, ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"])
    pg_engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")
    
    # 2. Conexão Destino
    BASE_DIR = Path(__file__).resolve().parent.parent
    sqlite_path = BASE_DIR / "data" / "anac_gold.db"
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")

    tabelas = ['dim_empresa', 'dim_aeroporto', 'fato_voo_mensal']
    
    logging.info(f"Iniciando cópia do PostgreSQL para {sqlite_path}...")
    for tabela in tabelas:
        logging.info(f"Copiando tabela: {tabela}...")
        df = pd.read_sql(f"SELECT * FROM {tabela}", pg_engine)
        df.to_sql(tabela, sqlite_engine, if_exists='replace', index=False)
        
    logging.info("Fallback SQLite gerado com sucesso!")

if __name__ == "__main__":
    exportar_para_sqlite()