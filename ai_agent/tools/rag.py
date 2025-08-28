"""
Tool for rag.search action
Connects to Milvus and uses DeepSeek/Gemini for embeddings.
Now supports authenticated Milvus (token or user/password) and secure (TLS) connections.
"""
import os
import requests
from typing import Dict, Any, Optional
from pymilvus import utility, connections, Collection
from ..llm_client import get_llm_client

# --- Milvus Admin Tool --- #
def _str_to_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _connect_to_milvus() -> None:
    """
    Establishes a Milvus connection using environment variables.

    Supported .env variables:
    - MILVUS_URI: full URI, e.g. "http://localhost:19530" or "https://cluster.api.zillizcloud.com"
    - MILVUS_HOST: host when URI not provided (default: localhost)
    - MILVUS_PORT: port when URI not provided (default: 19530)
    - MILVUS_TOKEN: prefer token auth when provided (e.g. Zilliz Cloud/token-based auth)
    - MILVUS_USER / MILVUS_PASSWORD: fallback auth pair (e.g. Milvus RBAC)
    - MILVUS_SECURE: "true/false" to enable TLS when using host/port (inferred from URI scheme if using MILVUS_URI)
    - MILVUS_SERVER_PEM: path to server CA cert when using TLS, if required
    """
    uri = os.getenv("MILVUS_URI")
    host = os.getenv("MILVUS_HOST", "localhost")
    port = os.getenv("MILVUS_PORT", "19530")
    token = os.getenv("MILVUS_TOKEN")
    user = os.getenv("MILVUS_USER")
    password = os.getenv("MILVUS_PASSWORD")
    server_pem = os.getenv("MILVUS_SERVER_PEM")

    # Determine secure flag
    if uri and uri.strip().lower().startswith("https"):
        secure = True
    else:
        secure = _str_to_bool(os.getenv("MILVUS_SECURE"))

    connect_kwargs: Dict[str, Any] = {}
    if uri:
        connect_kwargs["uri"] = uri
        connect_kwargs["secure"] = secure
        if server_pem and os.path.exists(server_pem):
            connect_kwargs["server_pem"] = server_pem
    else:
        # host/port mode
        connect_kwargs["host"] = host
        connect_kwargs["port"] = port
        if secure:
            connect_kwargs["secure"] = True
            if server_pem and os.path.exists(server_pem):
                connect_kwargs["server_pem"] = server_pem

    # Auth preference: token first, then user/password
    if token:
        connect_kwargs["token"] = token
        auth_mode = "token"
    elif user and password:
        connect_kwargs["user"] = user
        connect_kwargs["password"] = password
        auth_mode = "user/password"
    else:
        auth_mode = "no-auth"

    print(
        f"Connecting to Milvus using {('URI' if uri else 'host/port')} | "
        f"auth={auth_mode} | secure={'on' if secure else 'off'}"
    )
    connections.connect("default", **connect_kwargs)


def list_milvus_collections() -> dict:
    """
    Lists all collection names in the Milvus database.
    """
    try:
        _connect_to_milvus()
        print("Listing collections from Milvus...")
        names = utility.list_collections()
        return {"collections": names, "count": len(names)}
    except Exception as e:
        print(f"Error listing Milvus collections: {e}")
        return {"error": str(e), "count": 0, "collections": []}
    finally:
        try:
            connections.disconnect("default")
        except Exception:
            pass

def describe_milvus_index(collection: str) -> dict:
    """
    Describe the primary index configuration of a collection.
    Returns index_type, metric_type, and raw params when possible.
    """
    try:
        _connect_to_milvus()
        if not utility.has_collection(collection):
            return {"error": f"Collection '{collection}' does not exist", "indexes": []}
        col = Collection(collection)
        col.load()
        indexes_info = []
        for idx in col.indexes:
            raw_params = getattr(idx, "params", None)
            parsed = {}
            if isinstance(raw_params, dict):
                parsed = raw_params
            elif isinstance(raw_params, str):
                try:
                    import json as _json
                    parsed = _json.loads(raw_params)
                except Exception:
                    parsed = {"raw": raw_params}
            indexes_info.append(parsed)
        return {"collection": collection, "indexes": indexes_info}
    except Exception as e:
        return {"error": str(e), "indexes": []}
    finally:
        try:
            connections.disconnect("default")
        except Exception:
            pass

# --- Temporary DeepSeek Embedding Client --- #
# This will be moved to a dedicated client later
def get_embedding(text: str) -> list[float]:
    """
    Generates embedding for a given text using the DeepSeek API.
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY must be set in .env file")

    response = requests.post(
        f"{api_base}/embeddings",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "embedding.default", # Or another specific model
            "input": text
        }
    )
    response.raise_for_status()  # Raise an exception for bad status codes
    return response.json()["data"][0]["embedding"]

# --- Milvus Search Tool --- #

def search_milvus(
    query: str,
    top_k: int,
    collection: Optional[str] = None,
    collection_name: Optional[str] = None,
    metric_type: Optional[str] = None,
    anns_field: str = "embedding",
    params: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Performs a vector search in a Milvus collection.
    """
    # Accept both "collection" and legacy "collection_name"
    target_collection = collection or collection_name
    if not target_collection:
        return {"error": "Missing 'collection' parameter", "count": 0, "docs": [], "scores": []}

    try:
        # 1. Connect to Milvus
        _connect_to_milvus()

        # 2. Check if collection exists and is loaded
        if not utility.has_collection(target_collection):
            raise ValueError(f"Collection '{target_collection}' does not exist in Milvus.")
        collection_obj = Collection(target_collection)
        collection_obj.load()

        # 3. Generate embedding for the query
        print(f"Generating embedding for query: '{query}'")
        # Prefer Gemini via global llm_client
        query_vector = get_llm_client().get_embedding(query)

        # 4. Compose search parameters (auto-detect metric_type from index if not provided)
        detected_metric = None
        index_type = None
        try:
            if collection_obj.indexes:
                idx = collection_obj.indexes[0]
                # pymilvus: idx.params can be dict or JSON string
                raw_params = getattr(idx, "params", None)
                idx_params: Dict[str, Any] = {}
                if isinstance(raw_params, dict):
                    idx_params = raw_params
                elif isinstance(raw_params, str):
                    try:
                        import json as _json
                        idx_params = _json.loads(raw_params)
                    except Exception:
                        idx_params = {}
                detected_metric = (idx_params.get("metric_type") or idx_params.get("metricType") or "").upper() or None
                index_type = idx_params.get("index_type") or idx_params.get("indexType")
        except Exception:
            pass

        mt = (metric_type or detected_metric or os.getenv("MILVUS_DEFAULT_METRIC", "COSINE")).upper()
        # Build base params with sensible defaults
        search_params_inner: Dict[str, Any] = {}
        if params and isinstance(params, dict):
            search_params_inner.update(params)
        else:
            # Heuristic defaults based on index type
            if (index_type or "").upper() == "HNSW":
                search_params_inner.setdefault("ef", int(os.getenv("MILVUS_SEARCH_EF", "64")))
            else:
                search_params_inner.setdefault("nprobe", int(os.getenv("MILVUS_SEARCH_NPROBE", "10")))

        search_params = {"metric_type": mt, "params": search_params_inner}
        print(f"Executing RAG Search in '{target_collection}' with top_k={top_k} | metric={mt} | index={index_type}")
        
        results = collection_obj.search(
            data=[query_vector],
            anns_field=anns_field,
            param=search_params,
            limit=top_k,
            output_fields=["*"] # Get all metadata fields
        )

        # 5. Process and return results
        hits = results[0]
        scores = list(hits.distances)
        docs = [hit.entity.to_dict() for hit in hits]
        count = len(docs)

        return {"docs": docs, "scores": scores, "count": count}

    except Exception as e:
        print(f"Error during Milvus search: {e}")
        return {"error": str(e), "count": 0, "docs": [], "scores": []}
    finally:
        # Disconnect from Milvus
        try:
            connections.disconnect("default")
        except Exception:
            pass # Ignore if already disconnected