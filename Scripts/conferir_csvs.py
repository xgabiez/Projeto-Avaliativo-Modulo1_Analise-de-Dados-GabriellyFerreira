from pathlib import Path

import pandas as pd


pasta_raiz = Path(__file__).resolve().parent.parent
pasta_dados = pasta_raiz / "data"
arquivos = sorted(pasta_dados.glob("2025_*.csv"))

print(f"Arquivos encontrados: {len(arquivos)}")

for arquivo in arquivos:
    cabecalho = pd.read_csv(
        arquivo,
        sep=";",
        encoding="latin-1",
        nrows=0,
    )

    print(f"\nArquivo: {arquivo.name}")
    print(f"Quantidade de colunas: {len(cabecalho.columns)}")
    print(f"Colunas: {cabecalho.columns.tolist()}")