import os
import json
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv

from config import RECEITA_SCHEMA, SYSTEM_INSTRUCTION

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
CORS(app)

# Tempo máximo (segundos) para aguardar a resposta do modelo em ambiente serverless
TIMEOUT_SECONDS = 8


def _call_gemini(ingredientes):
    """Faz a chamada ao client do Gemini e retorna a string JSON.
    Pode levantar exceção que será tratada pelo chamador.
    """
    # Inicializa o cliente com a chave (cria por chamada para evitar problemas de import em ambientes serverless)
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não está definida no ambiente")
    client = genai.Client(api_key=GEMINI_API_KEY)

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


@app.route("/", methods=["GET"])
def status():
    return jsonify({
        "status": "success",
        "message": "API Gerador de Receitas funcionando!"
    }), 200


@app.route("/", methods=["POST"])
def generate():
    data = request.get_json()

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

    # Resultado da thread
    result = {}

    def worker():
        try:
            result_text = _call_gemini(ingredientes)
            result['text'] = result_text
        except Exception as e:
            result['error'] = str(e)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(TIMEOUT_SECONDS)

    if thread.is_alive():
        return jsonify({
            "status": "error",
            "message": f"Timeout: a geração demorou mais que {TIMEOUT_SECONDS} segundos. Tente novamente ou use backend com maior timeout."
        }), 504

    if 'error' in result:
        return jsonify({
            "status": "error",
            "message": f"Erro ao gerar a receita: {result['error']}"
        }), 500

    try:
        receita_estruturada = json.loads(result['text'])
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Resposta do modelo inválida: {str(e)}",
            "raw": result.get('text')
        }), 502

    return jsonify({
        "status": "success",
        "ingredientes_enviados": ingredientes,
        "dados_receita": receita_estruturada
    }), 200


if __name__ == "__main__":
    # Para testes locais (não usado pela Vercel)
    app.run(debug=True, host='0.0.0.0', port=5001)
