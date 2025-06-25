URLS= {
    "casas":"https://www.megaleiloes.com.br/imoveis/casas?tov=igbr&valor_max=5000000&tipo%5B0%5D=1&tipo%5B1%5D=2&pagina=",
    "apartamentos":"https://www.megaleiloes.com.br/imoveis/apartamentos?tov=igbr&valor_max=5000000&tipo%5B0%5D=1&tipo%5B1%5D=2&pagina=",
    "terrenos" : "https://www.megaleiloes.com.br/imoveis/terrenos-e-lotes?tov=igbr&valor_max=5000000&tipo%5B0%5D=1&tipo%5B1%5D=2&pagina="
}
CARD_CONTAINER_CLASS = "card-content"
SUMMARY_CLASS = "summary"

JSON_FILE = "data/leiloes_raspados_raw.json" # Nome do arquivo JSON de saída
DB_NAME = "data/imoveis_interessantes.db" # Nome do arquivo do banco de dados SQLite

OLLAMA_API_URL = "http://localhost:11434/api/generate" # URL da API do Ollama (ajuste se for diferente)
OLLAMA_MODEL = "gemma3:27b" # O modelo Ollama que você está usando (ex: llama3, mistral, etc.)
SCORE_THRESHOLD = 7 # Pontuação mínima para salvar o imóvel no banco de dados