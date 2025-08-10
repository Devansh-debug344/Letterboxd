# services/fetch_movies.py
import httpx

async def fetch_movies_from_api(name : str):
    url = f"http://www.omdbapi.com/?t={name}&apikey=afb3dcd"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()  
