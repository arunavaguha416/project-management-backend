import os
import requests


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


def is_ollama_running(timeout: float = 2.0) -> bool:
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def ollama_generate(prompt: str, temperature: float = 0.2, top_p: float = 0.9, timeout: int = 90) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p
            }
        },
        timeout=timeout
    )
    response.raise_for_status()
    return response.json().get("response", "")
