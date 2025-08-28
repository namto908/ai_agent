import os
from googleapiclient.discovery import build

def search(query: str):
    """
    Performs a Google search using the Custom Search JSON API.
    """
    print(f"--- Tool: GOOGLE SEARCH for query: {query} ---")
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key or not cse_id:
        return {"error": "GOOGLE_SEARCH_API_KEY and GOOGLE_CSE_ID environment variables are not set."}
        
    try:
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, num=5).execute()
        return res.get('items', [])
    except Exception as e:
        return {"error": f"An error occurred: {e}"}
