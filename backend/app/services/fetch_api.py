# services/fetch_movies.py
from app.config import setting
import httpx
from urllib.parse import quote
async def fetch_movies_from_api(id : str):

    url = f"https://www.omdbapi.com/?i=tt{id}&apikey={setting.omdb_api_key}"

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
