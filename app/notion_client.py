
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class NotionClient:

    BASE_URL = "https://api.notion.com/v1"

    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        self.version = os.getenv(
            "NOTION_VERSION",
            "2026-03-11"
        )

        if not self.token:
            raise ValueError(
                "NOTION_TOKEN não encontrado no arquivo .env"
            )

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.version,
            "Content-Type": "application/json"
        }

    def search(self, query="LifeOS"):
        response = requests.post(
            f"{self.BASE_URL}/search",
            headers=self.headers,
            json={
                "query": query,
                "page_size": 100
            },
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    def test_connection(self):
        result = self.search("LifeOS")
        return result.get("results", [])

    def query_data_source(self, data_source_id):
        url = (
            f"{self.BASE_URL}/data_sources/"
            f"{data_source_id}/query"
        )

        response = requests.post(
            url,
            headers=self.headers,
            json={"page_size": 100},
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    def get_data_source(self, data_source_id):
        url = (
            f"{self.BASE_URL}/data_sources/"
            f"{data_source_id}"
        )

        response = requests.get(
            url,
            headers=self.headers,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    def get_status_options(
        self,
        data_source_id,
        property_name="Status"
    ):
        data_source = self.get_data_source(data_source_id)

        properties = data_source.get("properties", {})
        status_property = properties.get(property_name)

        if not status_property:
            raise ValueError(
                f"Propriedade '{property_name}' não encontrada."
            )

        if status_property.get("type") != "status":
            raise ValueError(
                f"'{property_name}' não é uma propriedade Status."
            )

        options = status_property.get(
            "status", {}
        ).get("options", [])

        return [option["name"] for option in options]

    def update_page_status(
        self,
        page_id,
        new_status,
        property_name="Status"
    ):
        url = f"{self.BASE_URL}/pages/{page_id}"

        response = requests.patch(
            url,
            headers=self.headers,
            json={
                "properties": {
                    property_name: {
                        "status": {
                            "name": new_status
                        }
                    }
                }
            },
            timeout=30
        )

        response.raise_for_status()
        return response.json()
