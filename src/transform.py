import os
import sys
import logging
import re
from unicodedata import normalize
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_replace
from pyspark.sql.types import DoubleType

# 1. Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 2. Configuração de Caminhos Relativos Seguros
BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_PATH = BASE_DIR / 'data' / 'bronze' / "dados_estatisticos.csv"
SILVER_PATH = BASE_DIR / 'data' / 'silver' / "vra_condolidado"

def padronizar_nome_coluna(nome: str) -> str:
    """Remove acentos, caracteres especiais e converte para snake_case."""
    nome_sem_acento = normalize('NFKD', nome).encode('ASCII', 'ignore').decode("ASCII")
    nome_sujo = re.sub(r'[^\w\s]', '_', nome_sem_acento)
    nome_espacos = re.sub(r'\s+', '_', nome_sujo)
    return re.sub(r'_+', '_', nome_espacos).strip('_').lower()

def executar_transformacao():
    logger.info("Iniciando pipeline de transformação Bronze -> Silver...")

    # Garante o uso do Python do ambiente virtual nativamente
    os.environ['PYSPARK_PYTHON'] = sys.executable
    os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

    # Inicializa o Spark de forma silenciosa e otimizada
    spark = SparkSession.builder \
        .appName("ANAC_Transform_Bronze_to_Silver") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.parquet.compression.codec", "snappy") \
        .getOrCreate()
    
    # Reduz a verbosidade dos logs internos do Spark no Terminal
    spark.sparkContext.setLogLevel("ERROR")

    try:
        if not BRONZE_PATH.exists():
            raise FileNotFoundError(f"Arquivo base não encontrado em {BRONZE_PATH}")
        
        logger.info("Lendo dump da camada Bronze...")
        df_bronze = spark.read.csv(
            str(BRONZE_PATH),
            header=True,
            sep=';',
            encoding="ISO-8859-1",
            inferSchema=True
        )

        logger.info("Padronizando nomenclatura das colunas (snake_case)...")
        colunas_padronizadas = [padronizar_nome_coluna(c) for c in df_bronze.columns]
        df_silver = df_bronze.toDF(*colunas_padronizadas)

        logger.info("Aplicando higienização e casting de tipagens...")
        df_silver = df_silver.withColumn(
            "horas_voadas",
            regexp_replace(col("horas_voadas"), ",", ".").cast(DoubleType())
        )

        logger.info("Gravando camada Silver particionada por 'ano' em Parquet...")
        df_silver.write \
            .mode("overwrite") \
            .partitionBy("ano") \
            .parquet(str(SILVER_PATH))
        
        logger.info("Transformação concluída com sucesso absoluto!")
    
    except Exception as erro:
        logger.error(f"Falha crítica na transformação: {erro}")
        raise
    finally:
        # Ação obrigatória: Liberar a memória RAM derrubando a sessão.
        spark.stop()

if __name__ == "__main__":
    executar_transformacao()