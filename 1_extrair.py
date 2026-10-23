
"""
Etapa 1 - Extracao dos dados para a camada Raw.

Responsabilidades:
- Baixar o arquivo ZIP do Google Drive.
- Extrair os arquivos CSV.
- Carregar os dados nas tabelas Raw do MySQL.
"""

import logging
import zipfile
from pathlib import Path

import gdown
import pandas as pd

from config import (
    ARQUIVOS,
    CSV_ENCODING,
    CSV_SEPARADOR,
    DRIVE_FILE_ID,
    PASTA_DADOS,
    TAMANHO_BLOCO,
)

from banco import conectar, executar, inserir_em_lote


# Configuracao dos registros de execucao
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def baixar_arquivo() -> Path:
    """Baixa o arquivo ZIP do Google Drive."""

    # Cria a pasta data caso ela ainda nao exista
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)

    # Define onde o arquivo sera salvo
    caminho_zip = PASTA_DADOS / "viagens_2025.zip"

    try:
        logging.info("Iniciando download do arquivo do Google Drive.")

        resultado = gdown.download(
            id=DRIVE_FILE_ID,
            output=str(caminho_zip),
            quiet=False,
        )


        # Verifica se o download foi realizado
        if not resultado or not caminho_zip.exists():
            raise RuntimeError(
                "Download nao concluido. Verifique o ID "
                "e as permissoes do arquivo no Google Drive."
            )

        # Verifica se o arquivo baixado e realmente um ZIP
        if not zipfile.is_zipfile(caminho_zip):
            raise RuntimeError(
                "O arquivo baixado nao e um ZIP valido."
            )

        logging.info("Download concluido com sucesso.")

        return caminho_zip

    except Exception:
        logging.exception("Erro ao baixar o arquivo.")
        raise


def extrair_csvs(caminho_zip: Path) -> dict:
    """Extrai os quatro arquivos CSV do ZIP."""

    try:
        # Abre o arquivo ZIP para leitura
        with zipfile.ZipFile(caminho_zip, "r") as arquivo_zip:

            # Lista os nomes dos arquivos que estao no ZIP
            nomes_disponiveis = {
                Path(nome).name
                for nome in arquivo_zip.namelist()
                if not nome.endswith("/")
            }

            caminhos_csv = {}

            # Percorre os quatro arquivos definidos no config.py
            for nome, configuracao in ARQUIVOS.items():

                nome_csv = configuracao["csv"]

                # Confere se o arquivo existe dentro do ZIP
                if nome_csv not in nomes_disponiveis:
                    raise FileNotFoundError(
                        f"Arquivo {nome_csv} nao encontrado no ZIP."
                    )

                # Define o caminho de destino
                caminho_csv = PASTA_DADOS / nome_csv

                # Localiza o arquivo dentro do ZIP e salva o CSV
                with arquivo_zip.open(nome_csv) as origem:
                    with caminho_csv.open("wb") as destino:
                        destino.write(origem.read())

                # Guarda o caminho para usar na proxima etapa
                caminhos_csv[nome] = caminho_csv

                logging.info("Arquivo extraido: %s", nome_csv)

            return caminhos_csv

    except Exception:
        logging.exception("Erro ao extrair os arquivos CSV.")
        raise

if __name__ == "__main__":
    try:
        caminho_zip = baixar_arquivo()
        caminhos_csv = extrair_csvs(caminho_zip)

        print("\nDownload e extração concluídos!")

        for nome, caminho in caminhos_csv.items():
            print(f"{nome}: {caminho}")

    except Exception as erro:
        print(f"\nErro durante o teste: {erro}")