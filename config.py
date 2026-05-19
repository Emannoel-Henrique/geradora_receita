# Este dicionário diz ao Gemini exatamente quais campos ele deve responder
RECEITA_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "nome_da_receita": {"type": "STRING", "description": "O nome criativo da receita"},
        "porcoes": {"type": "STRING", "description": "Quantidade de porções (ex: '4 porções')"},
        "tempo_de_preparo": {"type": "STRING", "description": "Tempo estimado (ex: '45 minutos')"},
        "ingredientes": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Lista de ingredientes e suas respectivas quantidades"
        },
        "modo_de_preparo": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Passo a passo sequencial para preparar a receita"
        }
    },
    "required": ["nome_da_receita", "porcoes", "tempo_de_preparo", "ingredientes", "modo_de_preparo"]
}

SYSTEM_INSTRUCTION = """
Você é um Chef de Cozinha renomado. Sua tarefa é criar receitas incríveis utilizando prioritariamente os ingredientes fornecidos pelo usuário. 
Você pode sugerir ingredientes básicos extras (como sal, óleo, temperos) se necessário.
Você DEVE preencher todos os campos do esquema fornecido estritamente em português.
"""