import requests
import time
import logging
from pathlib import Path

# 1. Configuração do Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 2. Configurações Globais

URL_ANAC = "https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas/dados-estatisticos/arquivos/DadosEstatsticos.csv"
BRONZE_DIR = Path("./data/bronze")
ARQUIVO_DESTINO = BRONZE_DIR / "dados_estatisticos.csv"

def extrair_dados_anac(tentativas_maximas: int = 10) -> Path:
    """
    Faz o download do dump consolidado de dados estatísticos da ANAC
    """
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    tentativa = 1
    while tentativa <= tentativas_maximas:
        tamanho_local = ARQUIVO_DESTINO.stat().st_size if ARQUIVO_DESTINO.exists() else 0

        headers = {}
        if tamanho_local > 0:
            headers['Range'] = f'bytes={tamanho_local}-'
            logger.info(f"Tentativa {tentativa} / {tentativas_maximas} - Retomando de {tamanho_local / (1024 * 1024):.2f} MB...")
        else:
            logger.info(f"Tentativa {tentativa} / {tentativas_maximas} - Iniciando download do zero...")

        try:
            resposta = requests.get(URL_ANAC, headers=headers, stream=True, timeout=30)

            if resposta.status_code == 416:
                logger.info("Arquivo já baixado integralmente na camada Bronze")
                return ARQUIVO_DESTINO

            resposta.raise_for_status()

            modo_abertura = "ab" if resposta.status_code == 206 else "wb"
            if modo_abertura == "wb" and tamanho_local > 0:
                logger.warning("Servidor recusou retomar. Reiniciando arquivo...")
            
            with open(ARQUIVO_DESTINO, modo_abertura) as arquivo:
                for chunk in resposta.iter_content(chunk_size=1024*1024):
                    if chunk:
                        arquivo.write(chunk)
            
            logger.info(f"Sucesso! Dump consolidado salvo em: {ARQUIVO_DESTINO}")
            return ARQUIVO_DESTINO
        
        except requests.exceptions.ChunkedEncodingError:
            logger.warning("Servidor cortou a conexão. Retomaremos na próxima iteração.")
        except requests.exceptions.RequestException as erro:
            logger.error(f"Falha de rede: {erro}")
        except Exception as erro:
            logger.error(f"Erro inesperado: {erro}")
        
        tempo_espera = 3 * (2 ** (tentativa - 1))
        logger.info(f"Aguardando {tempo_espera} segundos antes da próxima tentativa...")
        time.sleep(tempo_espera)
        tentativa += 1
    
    logger.critical("Pipeline abortado: Limite máximo de tentativas atingido.")
    raise Exception("Falha crítica ao baixar o dump da ANAC.")

if __name__ == "__main__":
    logger.info("Iniciando processo de extração dos dados da ANAC...")
    extrair_dados_anac()