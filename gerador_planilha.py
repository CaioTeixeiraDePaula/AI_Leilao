import sqlite3
import pandas as pd
import re

# Função para remover caracteres ilegais
def remover_caracteres_ilegais(df):
    def limpar(texto):
        if isinstance(texto, str):
            return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", texto)
        return texto
    return df.applymap(limpar)

# Caminho para seu banco de dados SQLite
caminho_banco = 'data/imoveis_interessantes_mistral.db'

# Conectando ao banco
conn = sqlite3.connect(caminho_banco)
cursor = conn.cursor()

# Obtendo os nomes das tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tabelas = [linha[0] for linha in cursor.fetchall()]

# Criando o arquivo Excel com múltiplas planilhas
with pd.ExcelWriter("data/banco_convertido.xlsx") as writer:
    for tabela in tabelas:
        df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
        df = remover_caracteres_ilegais(df)
        df.to_excel(writer, sheet_name=tabela[:31], index=False)  # Excel aceita máx. 31 caracteres no nome da planilha

# Exportando também para CSV
for tabela in tabelas:
    df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
    df.to_csv(f"data/{tabela}.csv", index=False)

conn.close()
