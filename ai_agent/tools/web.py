"""
Mock Tool for http.get action
"""
import requests

def get_http(url: str, timeout: int) -> dict:
    """
    (Mock) Performs an HTTP GET request.
    """
    print(f"Executing HTTP GET: {url} with timeout={timeout}s")
    # In a real implementation, you might want more robust error handling
    # and content parsing.
    if "invalid" in url:
        return {"text": "", "status_code": 404, "error": "Not Found"}
        
    return {
        "text": "Đây là nội dung mẫu từ trang web.",
        "status_code": 200,
        "error": None
    }
