import os
import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv

from config import RECEITA_SCHEMA, SYSTEM_INSTRUCTION

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
CORS(app)


def get_gemini_client():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não encontrada. Configure a variável de ambiente na Vercel.")
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_recipe(ingredientes):
    client = get_gemini_client()

    lista_ingredientes = ", ".join(ingredientes)
    conteudo_prompt = f"Crie uma receita utilizando obrigatoriamente estes ingredientes: {lista_ingredientes}."

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=conteudo_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=RECEITA_SCHEMA,
        )
    )

    return response.text


@app.route("/")
def root():
    return send_from_directory(app.root_path, "index.html")


@app.route("/padeiro.jfif")
def baker_image():
    return send_from_directory(app.root_path, "padeiro.jfif")


@app.route("/status")
def status():
    return jsonify({
        "status": "success",
        "message": "API Gerador de Receitas funcionando!",
        "version": "1.0"
    }), 200


# Aceita as duas rotas para evitar erro no front
@app.route("/generate", methods=["POST"])
@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True)

    if not data or "ingredientes" not in data:
        return jsonify({
            "status": "error",
            "message": "Por favor, envie uma lista de ingredientes no formato JSON."
        }), 400

    ingredientes = data.get("ingredientes", [])

    if not isinstance(ingredientes, list) or len(ingredientes) < 3:
        return jsonify({
            "status": "error",
            "message": "Você precisa fornecer no mínimo 3 ingredientes."
        }), 400

    try:
        receita_json_string = generate_recipe(ingredientes)

        if not receita_json_string:
            return jsonify({
                "status": "error",
                "message": "A IA retornou uma resposta vazia."
            }), 502

        receita_estruturada = json.loads(receita_json_string)

        return jsonify({
            "status": "success",
            "ingredientes_enviados": ingredientes,
            "dados_receita": receita_estruturada
        }), 200

    except json.JSONDecodeError:
        return jsonify({
            "status": "error",
            "message": "A IA respondeu, mas não retornou um JSON válido."
        }), 502

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao gerar a receita: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(debug=True)