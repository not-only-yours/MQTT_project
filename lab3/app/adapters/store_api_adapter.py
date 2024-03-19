from typing import List
import requests
from fastapi import Response
from app.entities.processed_agent_data import ProcessedAgentData
import json
class StoreApiAdapter():
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]):
        try:
            print("processed agent data batch: " + str(len(processed_agent_data_batch)))
            print("processed agent data batch: " + str(processed_agent_data_batch))

            for item in processed_agent_data_batch:
                print(f"{self.api_base_url}/processed_agent_data/")
                print(item)
                response = requests.post(f"{self.api_base_url}/processed_agent_data/", json=item)
                response.raise_for_status()  # Raise an error for non-2xx responses

            return Response(content="OK", status_code=200)
        except Exception as e:
            print("Save data exception")
            return Response(content=f"Error: {e}", status_code=500)
