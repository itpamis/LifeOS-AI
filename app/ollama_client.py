
import requests


class OllamaClient:

    BASE_URL = "http://localhost:11434/api"

    def __init__(self, model="mistral:latest"):
        self.model = model

    def generate(self, prompt):

        response = requests.post(
            f"{self.BASE_URL}/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )

        response.raise_for_status()

        return response.json()["response"]

    def test_connection(self):

        response = requests.get(
            f"{self.BASE_URL}/tags",
            timeout=30
        )

        response.raise_for_status()

        return response.json()
