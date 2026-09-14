# services/fetch_movies.py
from app.config import setting
import httpx
from urllib.parse import quote

def normalize_id(id : str):
    id = id.strip()
    return id if id.startswith("tt") else f"tt{id}"

async def fetch_movies_from_api(id : str):

    url = f"https://www.omdbapi.com/?i={normalize_id(id)}&apikey={setting.omdb_api_key}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()  


async def fetch_movies_from_api_by_search(name : str):
    
    url = f"https://www.omdbapi.com/?s={quote(name)}&apikey={setting.omdb_api_key}"

    async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()  
