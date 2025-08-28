"""
LLM Client for interacting with various AI APIs (Custom/DeepSeek for Chat, Gemini for Embeddings).
"""
import os
import json
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from enum import Enum

class LLMProvider(str, Enum):
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    CUSTOM = "custom"

class AIClient:
    def __init__(self):
        # --- Chat Model Config ---
        self.llm_provider = os.getenv("LLM_PROVIDER", "deepseek").lower()
        self.chat_api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        self.chat_api_url = os.getenv("LLM_API_URL") or os.getenv("DEEPSEEK_API_URL")
        self.chat_model_id = os.getenv("LLM_MODEL_ID") or os.getenv("DEEPSEEK_MODEL_ID")

        if not all([self.chat_api_key, self.chat_api_url, self.chat_model_id]):
            raise ValueError(
                "LLM_API_KEY, LLM_API_URL, and LLM_MODEL_ID must be set in .env file"
            )

        # --- Embedding Model Config (Gemini) ---
        google_api_key = os.getenv("GEMINI_API_KEY")
        if not google_api_key:
            raise ValueError("GEMINI_API_KEY must be set in .env file for embeddings.")
        genai.configure(api_key=google_api_key)

    def _get_chat_headers(self):
        """Get headers based on LLM provider"""
        if self.llm_provider == LLMProvider.ANTHROPIC:
            return {
                "x-api-key": self.chat_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        else:
            return {
                "Authorization": f"Bearer {self.chat_api_key}",
                "Content-Type": "application/json"
            }

    def _format_messages_for_provider(self, prompt: str):
        """Format messages based on LLM provider"""
        if self.llm_provider == LLMProvider.ANTHROPIC:
            return {
                "model": self.chat_model_id,
                "max_tokens": 4096,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        else:
            return {
                "model": self.chat_model_id,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant that follows instructions precisely."},
                    {"role": "user", "content": prompt}
                ]
            }

    def _format_json_messages_for_provider(self, prompt: str):
        """Format messages for JSON mode based on LLM provider"""
        if self.llm_provider == LLMProvider.ANTHROPIC:
            return {
                "model": self.chat_model_id,
                "max_tokens": 4096,
                "messages": [
                    {"role": "user", "content": f"{prompt}\n\nYour response must be a valid JSON object and nothing else. Do not include markdown formatting."}
                ]
            }
        else:
            return {
                "model": self.chat_model_id,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant. Your response must be a valid JSON object and nothing else. Do not include markdown formatting like ```json."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }

    def _extract_content_from_response(self, response_json):
        """Extract content based on LLM provider"""
        if self.llm_provider == LLMProvider.ANTHROPIC:
            return response_json["content"][0]["text"]
        else:
            return response_json["choices"][0]["message"]["content"]

    def invoke_chat(self, prompt: str) -> str:
        """
        Invokes the configured chat completion model.
        """
        print(f"Invoking Chat Endpoint with model: {self.chat_model_id} ({self.llm_provider})")
        
        payload = self._format_messages_for_provider(prompt)
        response = requests.post(
            self.chat_api_url,
            headers=self._get_chat_headers(),
            json=payload
        )
        response.raise_for_status()
        
        content = self._extract_content_from_response(response.json())
        return content

    def invoke_chat_json(self, prompt: str) -> dict:
        """
        Invokes the chat model and expects a JSON string as output.
        """
        print(f"Invoking Chat Endpoint (JSON mode) with model: {self.chat_model_id} ({self.llm_provider})")
        
        payload = self._format_json_messages_for_provider(prompt)
        response = requests.post(
            self.chat_api_url,
            headers=self._get_chat_headers(),
            json=payload
        )
        response.raise_for_status()
        
        raw_content = self._extract_content_from_response(response.json())
        
        # Fix malformed JSON for DeepSeek
        if self.llm_provider == LLMProvider.DEEPSEEK:
            corrected_content = raw_content.replace("n  ", "\n  ").replace("n}", "\n}")
        else:
            corrected_content = raw_content

        return json.loads(corrected_content)

    def get_embedding(self, text: str, model: str = "models/text-embedding-004") -> list[float]:
        """
        Generates embedding for a given text using the Gemini API.
        """
        print(f"Generating embedding with Gemini model: {model}")
        return genai.embed_content(model=model, content=text)['embedding']

# Lazy singleton factory to avoid import-time crashes (e.g., in Streamlit)
_LLM_SINGLETON = None


def get_llm_client() -> AIClient:
    global _LLM_SINGLETON
    if _LLM_SINGLETON is not None:
        return _LLM_SINGLETON
    # Attempt to load env from common locations
    load_dotenv()  # current working dir
    # Also attempt to load .env next to this file's project root if exists
    try:
        here = os.path.dirname(os.path.dirname(__file__))  # ai_agent_project/ai_agent
        project_root = os.path.dirname(here)  # ai_agent_project
        env_path = os.path.join(project_root, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path, override=False)
    except Exception:
        pass

    _LLM_SINGLETON = AIClient()
    return _LLM_SINGLETON
