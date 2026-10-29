from flask import Flask, request
import requests
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

model = ChatGroq(model="openai/gpt-oss-20b", api_key=GROQ_API_KEY, temperature = 0.2)

API = "http://localhost:8080"
KEY = "projeto_alls"
INSTANCIA = "Teste"

app = Flask(__name__)


def enviar(destino, texto):
    r = requests.post(
        f"{API}/message/sendText/{INSTANCIA}",
        headers={"apikey": KEY},
        json={"number": destino, "text": texto},
        timeout=15,
    )
    if not r.ok:
        print("Erro ao enviar:", r.status_code, r.text)


@app.post("/webhook")
def webhook():
    body = request.get_json(silent=True) or {}
    event = body.get("event")
    data = body.get("data") or {}

    if event != "messages.upsert" or data.get("key", {}).get("fromMe"):
        return "", 200

    jid = data["key"]["remoteJid"]
    message = data.get("message") or {}
    texto = message.get("conversation") or (
        message.get("extendedTextMessage") or {}
    ).get("text")
    if not texto:
        return "", 200

    print(f"Recebida de {jid}: {texto}")

    msg = texto.strip().lower()
    response = model.invoke(msg)
    enviar(jid, response.content)

    return "", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)