import sys
from pathlib import Path

# Adiciona a raiz do projeto ao caminho de busca do Python.
pasta_raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pasta_raiz))

from banco import conectar

conexao = None

try:
    conexao = conectar()
    cursor = conexao.cursor()

    tabelas = [
        "raw_viagem",
        "raw_pagamento",
        "raw_passagem",
        "raw_trecho",
    ]

    print("\nCONTAGEM DE REGISTROS - CAMADA RAW\n")

    for tabela in tabelas:
        cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
        quantidade = cursor.fetchone()[0]

        print(f"{tabela}: {quantidade:,} registros")

    cursor.close()

except Exception as erro:
    print(f"Erro na validação: {erro}")

finally:
    if conexao and conexao.is_connected():
        conexao.close()
