
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

# Cabeçalhos originais dos CSVs
CABECALHOS_CSV = {
    "viagem": [
        "Identificador do processo de viagem",
        "Número da Proposta (PCDP)",
        "Situação",
        "Viagem Urgente",
        "Justificativa Urgência Viagem",
        "Código do órgão superior",
        "Nome do órgão superior",
        "Código órgão solicitante",
        "Nome órgão solicitante",
        "CPF viajante",
        "Nome",
        "Cargo",
        "Função",
        "Descrição Função",
        "Período - Data de início",
        "Período - Data de fim",
        "Destinos",
        "Motivo",
        "Valor diárias",
        "Valor passagens",
        "Valor devolução",
        "Valor outros gastos",
    ],
    "pagamento": [
        "Identificador do processo de viagem",
        "Número da Proposta (PCDP)",
        "Código do órgão superior",
        "Nome do órgão superior",
        "Codigo do órgão pagador",
        "Nome do órgao pagador",
        "Código da unidade gestora pagadora",
        "Nome da unidade gestora pagadora",
        "Tipo de pagamento",
        "Valor",
    ],
    "passagem": [
        "Identificador do processo de viagem",
        "Número da Proposta (PCDP)",
        "Meio de transporte",
        "País - Origem ida",
        "UF - Origem ida",
        "Cidade - Origem ida",
        "País - Destino ida",
        "UF - Destino ida",
        "Cidade - Destino ida",
        "País - Origem volta",
        "UF - Origem volta",
        "Cidade - Origem volta",
        "Pais - Destino volta",
        "UF - Destino volta",
        "Cidade - Destino volta",
        "Valor da passagem",
        "Taxa de serviço",
        "Data da emissão/compra",
        "Hora da emissão/compra",
    ],
    "trecho": [
        "Identificador do processo de viagem ",
        "Número da Proposta (PCDP)",
        "Sequência Trecho",
        "Origem - Data",
        "Origem - País",
        "Origem - UF",
        "Origem - Cidade",
        "Destino - Data",
        "Destino - País",
        "Destino - UF",
        "Destino - Cidade",
        "Meio de transporte",
        "Número Diárias",
        "Missao?",
    ],
}
# Mapeamento dos cabeçalhos originais dos CSVs
# para as colunas correspondentes nas tabelas Raw.
COLUNAS_RAW = {
    "viagem": [
        "id_viagem",
        "num_proposta",
        "situacao",
        "viagem_urgente",
        "justificativa_urgencia_viagem",
        "cod_orgao_superior",
        "nome_orgao_superior",
        "cod_orgao_solicitante",
        "nome_orgao_solicitante",
        "cpf_viajante",
        "nome_viajante",
        "cargo",
        "funcao",
        "descricao_funcao",
        "data_inicio",
        "data_fim",
        "destinos",
        "motivo",
        "valor_diarias",
        "valor_passagens",
        "valor_devolucao",
        "valor_outros_gastos",
    ],
    "pagamento": [
        "id_viagem",
        "num_proposta",
        "cod_orgao_superior",
        "nome_orgao_superior",
        "cod_orgao_pagador",
        "nome_orgao_pagador",
        "cod_ug_pagadora",
        "nome_ug_pagadora",
        "tipo_pagamento",
        "valor",
    ],
    "passagem": [
        "id_viagem",
        "num_proposta",
        "meio_transporte",
        "pais_origem_ida",
        "uf_origem_ida",
        "cidade_origem_ida",
        "pais_destino_ida",
        "uf_destino_ida",
        "cidade_destino_ida",
        "pais_origem_volta",
        "uf_origem_volta",
        "cidade_origem_volta",
        "pais_destino_volta",
        "uf_destino_volta",
        "cidade_destino_volta",
        "valor_passagem",
        "taxa_servico",
        "data_emissao",
        "hora_emissao",
    ],
    "trecho": [
        "id_viagem",
        "num_proposta",
        "sequencia_trecho",
        "origem_data",
        "origem_pais",
        "origem_uf",
        "origem_cidade",
        "destino_data",
        "destino_pais",
        "destino_uf",
        "destino_cidade",
        "meio_transporte",
        "numero_diarias",
        "missao",
    ],
}


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

    
def carregar_raw(conexao, caminhos_csv: dict) -> None:
    """Carrega os CSVs nas tabelas Raw em blocos."""

    for nome, configuracao in ARQUIVOS.items():
        caminho_csv = caminhos_csv[nome]
        tabela = configuracao["tabela_raw"]
        colunas = COLUNAS_RAW[nome]

        try:
            logging.info("Iniciando carga de %s em %s.", caminho_csv.name, tabela)

            # Confere os cabeçalhos antes de alterar a tabela.
            cabecalho = pd.read_csv(
                caminho_csv,
                sep=CSV_SEPARADOR,
                encoding=CSV_ENCODING,
                nrows=0,
                dtype=str,
            )
            # Confere se os nomes e a ordem dos cabeçalhos estão corretos.
            cabecalhos_esperados = CABECALHOS_CSV[nome]
            cabecalhos_encontrados = list(cabecalho.columns)

            if cabecalhos_encontrados != cabecalhos_esperados:
                logging.error("Cabeçalhos encontrados em %s:", caminho_csv.name)

                for indice, (encontrado, esperado) in enumerate(
                    zip(cabecalhos_encontrados, cabecalhos_esperados)
                ):
                    if encontrado != esperado:
                        logging.error(
                            "Coluna %s | Encontrado: %r | Esperado: %r",
                            indice + 1,
                            encontrado,
                            esperado,
                        )

                raise ValueError(
                    f"{caminho_csv.name}: cabeçalhos diferentes do esperado."
                )

            
            if len(cabecalho.columns) != len(colunas):
                raise ValueError(
                    f"{caminho_csv.name}: esperadas {len(colunas)} colunas, "
                    f"mas foram encontradas {len(cabecalho.columns)}."
                )

            if cabecalho.columns.duplicated().any():
                raise ValueError(
                    f"{caminho_csv.name}: existem cabeçalhos duplicados."
                )


            # Limpa a tabela para permitir executar a carga novamente.
            executar(conexao, f"TRUNCATE TABLE {tabela}")

            placeholders = ", ".join(["%s"] * len(colunas))
            nomes_colunas = ", ".join(f"`{coluna}`" for coluna in colunas)

            sql_insert = (
                f"INSERT INTO {tabela} ({nomes_colunas}) "
                f"VALUES ({placeholders})"
            )

            total = 0

            for bloco in pd.read_csv(
                caminho_csv,
                sep=CSV_SEPARADOR,
                encoding=CSV_ENCODING,
                dtype=str,
                keep_default_na=False,
                chunksize=TAMANHO_BLOCO,
            ):
             

                linhas = list(bloco.itertuples(index=False, name=None))
                inserir_em_lote(conexao, sql_insert, linhas)

                total += len(linhas)
                logging.info(
                    "%s: %s registros carregados.",
                    tabela,
                    total,
                )

            logging.info(
                "Carga concluída: %s registros em %s.",
                total,
                tabela,
            )

        except Exception:
            logging.exception("Erro durante a carga da tabela %s.", tabela)
            raise


if __name__ == "__main__":
    conexao = None

    try:
        caminho_zip = baixar_arquivo()
        caminhos_csv = extrair_csvs(caminho_zip)

        conexao = conectar()
        carregar_raw(conexao, caminhos_csv)

        print("\nExtração e carga Raw concluídas!")

    except Exception as erro:
        logging.error("O processo foi interrompido: %s", erro)
        print(f"\nErro durante o processo: {erro}")

    finally:
        if conexao and conexao.is_connected():
            conexao.close()


