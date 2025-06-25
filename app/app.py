import streamlit as st
import pandas as pd
import sqlite3

# Conectar ao banco
conn = sqlite3.connect('data/imoveis_interessantes_mistral.db')
df = pd.read_sql("SELECT * FROM imoveis", conn)

st.title("Imóveis em Leilão - Visualizador")

# Contagem de imóveis por cidade
contagem = df['localidade_pagina_principal'].value_counts().to_dict()

# Gerar lista de opções com quantidade
opcoes = [f"{cidade} ({contagem[cidade]})" for cidade in sorted(contagem.keys())]

# Selectbox
cidade_selecionada = st.selectbox("Selecione a cidade:", opcoes)

# Extrair cidade
cidade = cidade_selecionada.split(' (')[0]

# Filtrar
df_filtrado = df[df['localidade_pagina_principal'] == cidade]

# Mostrar cards
for _, row in df_filtrado.iterrows():
    st.subheader(row['titulo'])
    st.markdown(f"**Preço:** {row['preco']}")
    st.markdown(f"**Localização:** {row['localizacao_detalhada']}")
    st.markdown(f"**Leiloeiro:** {row['leiloeiro']}")
    st.markdown(f"[🔗 Link para o leilão]({row['link_detalhes']})")
    with st.expander("📝 Descrição completa"):
        st.write(row['descricao_completa'])
    with st.expander("✅ Pontos Positivos"):
        st.write(row['pontos_positivos'])
    with st.expander("⚠️ Pontos Negativos"):
        st.write(row['pontos_negativos'])
    st.divider()
