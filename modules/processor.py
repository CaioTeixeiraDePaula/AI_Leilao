# processor.py
import json
import sqlite3
import os 
import requests # Para fazer requisições HTTP para a API do Ollama
import time # Para um pequeno atraso entre as chamadas da LLM

# --- Configurações ---
INPUT_RAW_JSON_FILE = "data/leiloes_raspados_raw.json" # Arquivo JSON gerado pelo scraper
DB_NAME = "data/imoveis_interessantes_mistral.db" # Nome do arquivo do banco de dados SQLite
OLLAMA_API_URL = "http://localhost:11434/api/generate" # URL da API do Ollama (ajuste se for diferente)
OLLAMA_MODEL = "llama3.2" # O modelo Ollama que você está usando (ex: llama3, mistral, etc.)
SCORE_THRESHOLD = 7 # Pontuação mínima para salvar o imóvel no banco de dados

# --- Função para Avaliar Imóvel com Ollama ---
def evaluate_property_with_ollama(property_data: dict) -> dict:
    """
    Avalia um imóvel usando um modelo do Ollama, retornando pontuação, 
    pontos positivos e negativos.

    Args:
        property_data (dict): Dicionário contendo todos os dados do imóvel.

    Returns:
        dict: Um dicionário com 'score' (int), 'positives' (str) e 'negatives' (str).
              Retorna valores padrão (0, "Erro", "Erro") em caso de falha.
    """
    print(f"  > Avaliando imóvel '{property_data.get('titulo')}' com Ollama...")

    # Prepara o prompt para o Ollama
    # Agora pedimos um JSON para facilitar a extração dos dados
    prompt_text = f"""
    Com base nos dados do seguinte imóvel de leilão, avalie sua atratividade e oportunidade de investimento em uma escala de 0 a 10, onde 0 é "nada interessante" e 10 é "extremamente interessante".

    Considere os seguintes critérios:
    - Preço: Um preço baixo em relação às características do imóvel é um ponto positivo.
    - Descrição Completa: Clareza, detalhamento e ausência de problemas graves (dívidas excessivas, problemas estruturais) são positivos.
    - Localização Detalhada: Precisão e potencial de valorização da área são importantes.
    - Condições de Pagamento: Flexibilidade nas condições é um ponto positivo.

    Dados do Imóvel:
    {json.dumps(property_data, ensure_ascii=False, indent=2)}

    Responda APENAS com um objeto JSON no seguinte formato:
    {{
      "score": <número inteiro de 0 a 10>,
      "positives": "<Pontos positivos do imóvel em uma frase, separado por vírgulas se houver mais de um.>",
      "negatives": "<Pontos negativos do imóvel em uma frase, separado por vírgulas se houver mais de um.>"
    }}
    """

    default_response = {"score": 0, "positives": "Erro na avaliação", "negatives": "Erro na avaliação"}

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt_text,
            "stream": False, 
            "options": {
                "temperature": 0.2, # Um pouco mais de variação, mas ainda controlada
                "top_k": 40,
                "top_p": 0.9,
            }
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(OLLAMA_API_URL, json=payload, headers=headers, timeout=250) # Aumentei o timeout
        response.raise_for_status() 
        
        response_json_content = response.json().get("response", "").strip()
        
        # Tenta parsear a resposta como JSON
        try:
            llm_output = json.loads(response_json_content)
            
            score = llm_output.get("score")
            positives = llm_output.get("positives", "N/A")
            negatives = llm_output.get("negatives", "N/A")

            # Valida a pontuação
            if isinstance(score, int) and 0 <= score <= 10:
                print(f"  > Avaliação do Ollama para '{property_data.get('titulo')}': Pontuação: {score}/10.")
                return {"score": score, "positives": positives, "negatives": negatives}
            else:
                print(f"  > Ollama retornou pontuação inválida: '{score}'. Retornando 0.")
                return default_response

        except json.JSONDecodeError:
            print(f"  > Ollama retornou JSON inválido: '{response_json_content}'. Retornando padrão.")
            return default_response
            
    except requests.exceptions.RequestException as e:
        print(f"  > Erro ao chamar a API do Ollama: {e}. Retornando padrão.")
        return default_response
    except Exception as e:
        print(f"  > Ocorreu um erro inesperado na avaliação do Ollama: {e}. Retornando padrão.")
        return default_response
    
    # --- Lógica de simulação alternativa se o Ollama não estiver configurado ---
    # Esta parte será executada se a chamada real ao Ollama falhar ou estiver comentada.
    # Você pode remover esta simulação quando a integração real estiver funcionando.
    # print("  > Usando lógica de simulação para a avaliação do Ollama.")
    # if "descricao_completa" in property_data and len(property_data["descricao_completa"]) > 200:
    #     try:
    #         price_str = property_data.get("preco", "R$ 0,00").replace("R$", "").replace(".", "").replace(",", ".").strip()
    #         price_value = float(price_str)
    #         if price_value < 500000:
    #             return 8 # Exemplo de pontuação alta
    #         elif price_value < 1000000:
    #             return 6 # Exemplo de pontuação média
    #     except ValueError:
    #         pass
    # return 3 # Pontuação baixa para outros casos na simulação

# --- Configuração do Banco de Dados SQLite ---
def setup_database(db_name: str):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS imoveis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            preco TEXT,
            localidade_pagina_principal TEXT,
            numero_leilao TEXT,
            link_detalhes TEXT UNIQUE, 
            localizacao_detalhada TEXT,
            vara TEXT,
            forum TEXT,
            leiloeiro TEXT,
            descricao_completa TEXT,
            condicoes_pagamento TEXT,
            pontuacao_ollama INTEGER, 
            pontos_positivos TEXT,     -- Nova coluna
            pontos_negativos TEXT,    -- Nova coluna
            data_avaliacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Banco de dados '{db_name}' configurado com sucesso.")

def insert_property_into_db(db_name: str, property_data: dict, evaluation_results: dict):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO imoveis (
                titulo, preco, localidade_pagina_principal, numero_leilao, link_detalhes,
                localizacao_detalhada, vara, forum, leiloeiro, descricao_completa, condicoes_pagamento,
                pontuacao_ollama, pontos_positivos, pontos_negativos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            property_data.get("titulo"),
            property_data.get("preco"),
            property_data.get("localidade_pagina_principal"),
            property_data.get("numero_leilao"),
            property_data.get("link_detalhes"),
            property_data.get("localizacao_detalhada"),
            property_data.get("vara"),
            property_data.get("forum"),
            property_data.get("leiloeiro"),
            property_data.get("descricao_completa"),
            property_data.get("condicoes_pagamento"),
            evaluation_results.get("score"),
            evaluation_results.get("positives"),
            evaluation_results.get("negatives")
        ))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"  > Imóvel '{property_data.get('titulo')}' (Pontuação: {evaluation_results.get('score')}) inserido no banco de dados.")
        else:
            print(f"  > Imóvel '{property_data.get('titulo')}' (Pontuação: {evaluation_results.get('score')}) já existe no banco de dados (ignorando).")
    except sqlite3.Error as e:
        print(f"Erro ao inserir imóvel '{property_data.get('titulo')}' no DB: {e}")
    finally:
        conn.close()

def process_and_save_data(input_json_file: str, db_name: str, score_threshold: int):
    print(f"Iniciando o processamento de dados do arquivo '{input_json_file}'...")
    print(f"Apenas imóveis com pontuação Ollama >= {score_threshold} serão salvos.")
    
    if not os.path.exists(input_json_file):
        print(f"Erro: Arquivo '{input_json_file}' não encontrado. Execute o scraper primeiro.")
        return

    setup_database(db_name)

    try:
        with open(input_json_file, 'r', encoding='utf-8') as f:
            all_raw_data = json.load(f)
        print(f"Carregados {len(all_raw_data)} imóveis para avaliação.")
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON de '{input_json_file}'. O arquivo pode estar corrompido ou vazio.")
        return
    except Exception as e:
        print(f"Erro ao ler o arquivo JSON: {e}")
        return

    total_evaluated = 0
    total_interesting_saved = 0

    for item_data in all_raw_data:
        total_evaluated += 1
        
        # --- AVALIAÇÃO COM OLLAMA ---
        # A função agora retorna um dicionário com score, positives e negatives
        evaluation_results = evaluate_property_with_ollama(item_data)
        
        if evaluation_results["score"] >= score_threshold:
            insert_property_into_db(db_name, item_data, evaluation_results)
            total_interesting_saved += 1
        else:
            print(f"  > Imóvel '{item_data.get('titulo', 'N/A')}' pontuação {evaluation_results['score']}/10, abaixo do limiar de {score_threshold}. Ignorando.")
            # Opcional: Você pode salvar os pontos negativos/positivos de *todos* os imóveis
            # em um log separado, mesmo os não interessantes, para análise futura.
            
        time.sleep(1.0) # Aumentei o atraso para dar tempo ao Ollama e evitar erros

    print(f"\nProcessamento concluído. Avaliados {total_evaluated} imóveis.")
    print(f"Total de {total_interesting_saved} imóveis considerados interessantes (pontuação >= {score_threshold}) e salvos em '{db_name}'.")

if __name__ == "__main__":
    process_and_save_data(INPUT_RAW_JSON_FILE, DB_NAME, SCORE_THRESHOLD)