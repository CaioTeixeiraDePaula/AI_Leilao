from bs4 import BeautifulSoup
import requests
import re 
import json
import time

URL_BASE = "https://www.megaleiloes.com.br/Pesquisa?tov=igbr&valor_max=5000000&tipo%5B0%5D=1&tipo%5B1%5D=2&pagina="

CARD_CONTAINER_CLASS = "card-content"
SUMMARY_CLASS = "summary" 
OUTPUT_JSON_FILE = "data/leiloes_raspados_raw.json" # Nome do arquivo JSON de saída

# --- Funções Auxiliares ---
def get_total_pages(soup: BeautifulSoup, summary_class: str) -> int:
    """
    Extrai o número total de páginas do elemento de sumário.
    """
    summary_element = soup.find("div", class_=summary_class)
    if summary_element:
        summary_text = summary_element.text.strip()
        match = re.search(r'Página \d+ de (\d+)', summary_text)
        if match:
            return int(match.group(1)) 
    return 1 

# --- Função para raspar a página de descrição do leilão ---
def scrap_description_page(description_url: str, title: str, time_delay:int) -> dict:
    """
    Visita a página de detalhes de um leilão e extrai informações adicionais.
    Retorna um dicionário com os detalhes extraídos.
    """
    details = {
        "localizacao_detalhada": "Não encontrada",
        "vara": "Não encontrada",
        "forum": "Não encontrado",
        "leiloeiro": "Não encontrado",
        "descricao_completa": "Não encontrada",
        "condicoes_pagamento": "Não encontradas"
    }

    if not description_url or description_url == "Link não encontrado":
        print(f"  > Link de detalhes não disponível para o leilão '{title}'.")
        return details

    print(f"  > Visitando página de detalhes para '{title}': {description_url}")
    
    time.sleep(time_delay) # Atraso de 1.5 segundo entre as requisições de detalhes (ajustado um pouco)

    try:
        response = requests.get(description_url)
        response.raise_for_status()

        soup_details = BeautifulSoup(response.text, "html.parser")

        # --- Extração de Detalhes da Página de Detalhes ---
        # Localização Detalhada
        locality_elem = soup_details.select_one("div.locality div.value") 
        if locality_elem:
            details["localizacao_detalhada"] = locality_elem.get_text(strip=True)

        # Vara (Jurisdição)
        vara_elem = soup_details.select_one("div.jurisdiction div.value")
        if vara_elem:
            details["vara"] = vara_elem.get_text(strip=True)

        # Forum
        forum_elem = soup_details.select_one("div.forum div.value")
        if forum_elem:
            details["forum"] = forum_elem.get_text(strip=True)

        # Leiloeiro
        leiloeiro_elem = soup_details.select_one("div.author div.value")
        if leiloeiro_elem:
            details["leiloeiro"] = leiloeiro_elem.get_text(strip=True)

        # Descrição Completa (conteúdo dentro de div#tab-description div.content)
        description_content_elem = soup_details.select_one("div#tab-description div.content")
        if description_content_elem:
            details["descricao_completa"] = description_content_elem.get_text(separator="\n", strip=True)

        # Condições de Pagamento (conteúdo dentro de div#tab-contract div.content)
        # Note que div#tab-contract também tem a classe 'tab-pane'
        payment_conditions_content_elem = soup_details.select_one("div#tab-contract div.content")
        if payment_conditions_content_elem:
            details["condicoes_pagamento"] = payment_conditions_content_elem.get_text(separator="\n", strip=True)

    except requests.exceptions.RequestException as e:
        print(f"  > Erro ao fazer a requisição para a página de detalhes de '{title}': {e}") 
    except Exception as e:
        print(f"  > Ocorreu um erro inesperado ao raspar detalhes de '{title}': {e}")
    
    return details 

# --- Função principal de scraping ---
def run_scrap(base_url: str, card_container_class: str, summary_class: str, output_file: str, time_delay:float = 1.5):
    all_extracted_data = [] 
    current_page = 1
    total_pages = 1 

    # Tenta carregar dados existentes do arquivo JSON
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            all_extracted_data = json.load(f)
        print(f"Carregados {len(all_extracted_data)} itens existentes de '{output_file}'.")
    except FileNotFoundError:
        print(f"Arquivo '{output_file}' não encontrado. Começando um novo arquivo.")
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON de '{output_file}'. O arquivo pode estar corrompido ou vazio. Começando um novo arquivo.")
        all_extracted_data = [] # Reinicia se o JSON estiver corrompido

    # Otimização: se já carregamos dados, podemos tentar continuar da última página raspada
    if all_extracted_data:
        # A URL que você forneceu termina com "&pagina=", então podemos extrair a última página
        # do último link de detalhes raspado, se disponível
        last_item_link = all_extracted_data[-1].get("link_detalhes")
        if last_item_link:
            match = re.search(r'&pagina=(\d+)', last_item_link)
            if match:
                # Tentamos retomar da página seguinte à última raspada
                # (ou da mesma página se o último item foi o primeiro daquela página)
                # No entanto, essa lógica pode ser falha se a ordem dos itens mudar ou se a página
                # estiver cheia e não houver um item raspado correspondente à última página.
                # Para simplificar e garantir a continuidade do fluxo de paginação,
                # vamos manter o `current_page = 1` e confiar no filtro de dados duplicados
                # se você precisar dele (não implementado aqui, mas é uma consideração).
                pass # Nenhuma ação aqui, a página começa em 1

    while current_page <= total_pages:
        page_url = f"{base_url}{current_page}"
        print(f"\nRaspando página principal: {page_url}")

        try:
            response = requests.get(page_url)
            response.raise_for_status()

            main_page_soup = BeautifulSoup(response.text, "html.parser")

            if current_page == 1:
                total_pages = get_total_pages(main_page_soup, summary_class)
                print(f"Total de páginas a raspar: {total_pages}\n")
                if total_pages == 1: 
                     print("Atenção: Apenas uma página principal encontrada, verificando se há conteúdo.")

            auction_cards = main_page_soup.find_all("div", class_=card_container_class)

            if not auction_cards:
                print(f"Nenhum card com a classe '{card_container_class}' encontrado na página {current_page}. Parando o scraping.")
                break 

            current_page_data = [] 

            for card in auction_cards:
                name_tag = card.select_one("a.card-title") 
                price_tag = card.select_one("div.card-price")
                locality_tag_main = card.select_one("a.card-locality") # Localidade da página principal
                number_tag = card.select_one("div.card-number")

                name = name_tag.text.strip() if name_tag else "Título não encontrado"
                price = price_tag.text.strip() if price_tag else "Preço não encontrado"
                # Usar a localidade da página principal aqui, a detalhada virá do scrap_description_page
                locality_main = locality_tag_main.text.strip() if locality_tag_main else "Localidade (principal) não encontrada"
                auction_number = number_tag.text.strip() if number_tag else "Número do leilão não encontrado"
                title_link = name_tag.get('href') if name_tag else "Link não encontrado"

                print(f"--- Processando Item: '{name}' (Página {current_page}) ---")
                
                # Chamando a função de scraping da página de detalhes
                additional_details = scrap_description_page(description_url=title_link, title=name, time_delay=time_delay)
                
                # Combinar os dados da página principal com os da página de detalhes
                combined_data = {
                    "titulo": name,
                    "preco": price,
                    "localidade_pagina_principal": locality_main, # Para diferenciar da detalhada
                    "numero_leilao": auction_number,
                    "link_detalhes": title_link,
                    **additional_details 
                }
                current_page_data.append(combined_data) 
                
            # Salvar dados desta página na lista geral e então no arquivo JSON
            all_extracted_data.extend(current_page_data) 
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_extracted_data, f, ensure_ascii=False, indent=4)
            print(f"Salvos {len(current_page_data)} novos itens da página {current_page}. Total acumulado: {len(all_extracted_data)} itens em '{output_file}'.")
            
            current_page += 1 

        except requests.exceptions.RequestException as e:
            print(f"Erro ao fazer a requisição na página {current_page}: {e}. Parando o scraping.")
            break 
        except Exception as e:
            print(f"Ocorreu um erro inesperado na página {current_page}: {e}. Parando o scraping.")
            break 
    
    print(f"\nProcesso de scraping concluído. Total final de {len(all_extracted_data)} itens raspados de {total_pages} páginas.")
    # Garante que o arquivo final está atualizado, mesmo se houve um break
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_extracted_data, f, ensure_ascii=False, indent=4)
    print(f"Todos os dados finais salvos em '{output_file}'.")


if __name__ == "__main__":
    run_scrap(base_url=URL_BASE, 
              card_container_class=CARD_CONTAINER_CLASS,
              summary_class=SUMMARY_CLASS,
              output_file=OUTPUT_JSON_FILE)