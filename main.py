import streamlit as st
import pandas as pd
import sqlite3
from configs import *
from modules import *

# Função que roda o scraping e salva no banco
def rodar_scraper_e_processar():
    for classification in URLS:
        run_scrap(
            base_url=URLS[classification], 
            card_container_class=CARD_CONTAINER_CLASS,
            summary_class=SUMMARY_CLASS,
            output_file=JSON_FILE,
            time_delay=0.15
        )

        process_and_save_data(
            input_json_file=JSON_FILE,
            db_name=DB_NAME,
            score_threshold=7    
        )

st.title("Imóveis em Leilão - Visualizador")

# 🔥 Botão para executar o scraper
if st.button("🔄 Atualizar Dados (Rodar Scraper)"):
    with st.spinner("Executando scraping e atualizando banco de dados..."):
        rodar_scraper_e_processar()
    st.success("Dados atualizados com sucesso!")

# Conectar ao banco atualizado
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM imoveis", conn)

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
