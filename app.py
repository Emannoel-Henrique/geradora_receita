# app.py (Parte 1)
import os
import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Importando o que criamos no outro arquivo:
from config import RECEITA_SCHEMA, SYSTEM_INSTRUCTION

# Carrega as variáveis de ambiente e inicia o Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Inicializa o Flask
app = Flask(__name__)
CORS(app)

# app.py (Parte 2)

def generate_recipe(ingredientes):
    # Junta os ingredientes enviados em uma única linha de texto
    lista_ingredientes = ", ".join(ingredientes)
    conteudo_prompt = f"Crie uma receita utilizando obrigatoriamente estes ingredientes: {lista_ingredientes}."
    
    # Faz a chamada para o modelo pedindo uma resposta estruturada em JSON
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=conteudo_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json", # Força a saída em formato JSON
            response_schema=RECEITA_SCHEMA,       # Segue o esquema do config.py
        )
    )
    return response.text

# app.py (Parte 3)

@app.route("/")
def root():
    return send_from_directory(app.root_path, 'index.html')

@app.route("/padeiro.jfif")
def baker_image():
    return send_from_directory(app.root_path, 'padeiro.jfif')

@app.route("/status")
def status():
    return jsonify({
        "status": "success",
        "message": "API Gerador de Receitas funcionando!",
        "version": "1.0"
    }), 200

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    
    # Validação 1: O JSON foi enviado?
    if not data or "ingredientes" not in data:
        return jsonify({
            "status": "error",
            "message": "Por favor, envie uma lista de ingredientes no formato JSON."
        }), 400
        
    ingredientes = data.get("ingredientes", [])
    
    # Validação 2: É uma lista e possui no mínimo 3 itens?
    if not isinstance(ingredientes, list) or len(ingredientes) < 3:
        return jsonify({
            "status": "error",
            "message": "Você precisa fornecer no mínimo 3 ingredientes."
        }), 400
    
    try:
        # Pede para o Gemini gerar a receita (retorna como string JSON)
        receita_json_string = generate_recipe(ingredientes)
        
        # Converte a string JSON em Dicionário Python para o Flask organizar a resposta
        receita_estruturada = json.loads(receita_json_string)
        
        return jsonify({
            "status": "success",
            "ingredientes_enviados": ingredientes,
            "dados_receita": receita_estruturada
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao gerar a receita: {str(e)}"
        }), 500

# Executa o servidor local
if __name__ == "__main__":
    app.run(debug=True)
