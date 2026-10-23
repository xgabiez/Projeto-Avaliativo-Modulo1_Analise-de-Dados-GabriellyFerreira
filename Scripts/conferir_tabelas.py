import sys
from pathlib import Path

pasta_raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pasta_raiz))

from banco import conectar

conexao = None

try:
    conexao = conectar()
    cursor = conexao.cursor()

    tabelas_raw = [
        "raw_viagem",
        "raw_pagamento",
        "raw_passagem",
        "raw_trecho",
    ]

    for tabela in tabelas_raw:
        cursor.execute(f"DESCRIBE {tabela}")
        colunas = cursor.fetchall()

        print(f"\n{tabela}: {len(colunas)} colunas")

        for coluna in colunas:
            print(f"  {coluna[0]} — {coluna[1]}")

    cursor.execute("SHOW TABLES LIKE 'silver_viagem'")
    resultado = cursor.fetchone()

    print(
        "\nTabela silver_viagem:",
        "EXISTE" if resultado else "NÃO EXISTE",
    )

    cursor.close()

except Exception as erro:
    print(f"Erro ao consultar o banco: {erro}")

finally:
    if conexao and conexao.is_connected():
        conexao.close()
