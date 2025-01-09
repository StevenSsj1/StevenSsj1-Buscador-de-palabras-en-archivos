from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Annotated, Optional
from elasticsearch import AsyncElasticsearch
from datetime import datetime

BASE_URL = "elasticsearch:9200"
client = AsyncElasticsearch(BASE_URL)
router = APIRouter(prefix="/api_documents", tags=["api_documents"])

class ParamsGetDocuments(BaseModel):
    name_index: str = "pdfs"
    id_index: int

class Document(BaseModel):
    name_document: str
    content: str
    page_number: Optional[int] = None
    total_pages: Optional[int] = None

@router.get("/documents/")
async def get_all_documents():
    result = await client.search(
        index="pdfs",
        body={"query": {"match_all": {}}}
    )
    return result

@router.get("/document/")
async def get_document_by_index(params_documents: Annotated[ParamsGetDocuments, Query()]):
    try:
        resp = await client.get(index=params_documents.name_index, id=params_documents.id_index)
        return resp
    except Exception as e:
        return {"error": str(e)}

@router.get("/search/")
async def search_documents(
    search_term: Annotated[Optional[str], Query()] = None,
    index_name: Annotated[str, Query()] = "pdfs",
):
    # Construcción de la consulta de búsqueda
    if search_term:
        query = {
            "query": {
                "multi_match": {
                    "query": search_term,
                    "fields": ["name_document^2", "content"],
                    "fuzziness": "AUTO"
                }
            },
            "_source": ["name_document", "page_number", "content", "total_pages"],
            "highlight": {
                "fields": {
                    "content": {
                        "number_of_fragments": 3,
                        "fragment_size": 150
                    }
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            }
        }
    else:
        query = {
            "query": {
                "match_all": {}
            },
            "_source": ["name_document", "page_number", "content", "total_pages"],
            "highlight": {
                "fields": {
                    "content": {
                        "number_of_fragments": 3,
                        "fragment_size": 150
                    }
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            }
        }

    try:
        # Ejecución de la consulta de búsqueda en Elasticsearch
        response = await client.search(index=index_name, body=query)

        # Formateo de los resultados de la búsqueda
        formatted_results = {
            "total_hits": response["hits"]["total"]["value"],
            "results": [{
                "document_name": hit["_source"]["name_document"],
                "page_number": hit["_source"]["page_number"],
                "content": hit["_source"].get("content", ""),  # Asegurarse de incluir el contenido

                "total_pages": hit["_source"]["total_pages"],
                "highlights": hit.get("highlight", {}).get("content", [])
            } for hit in response["hits"]["hits"]]
        }
        return formatted_results
    except Exception as e:
        # Manejo de errores
        return {"error": str(e)}

@router.get("/exact_search/")
async def exact_search_documents(
    search_term: Annotated[str, Query()],
    index_name: Annotated[str, Query()] = "pdfs",
):
    # Construcción de la consulta de búsqueda exacta
    query = {
        "query": {
            "match_phrase": {
                "content": search_term
            }
        },
        "highlight": {
            "fields": {
                "content": {
                    "number_of_fragments": 3,
                    "fragment_size": 150
                }
            },
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"]
        },
        "sort": [{"page_number": "asc"}]
    }

    try:
        # Ejecución de la consulta de búsqueda en Elasticsearch
        response = await client.search(index=index_name, body=query)

        # Formateo de los resultados de la búsqueda
        formatted_results = {
            "total_hits": response["hits"]["total"]["value"],
            "results": [{
                "document_name": hit["_source"]["name_document"],
                "page_number": hit["_source"]["page_number"],
                "content": hit["_source"].get("content", ""),  # Asegurarse de incluir el contenido
                "total_pages": hit["_source"]["total_pages"],
                "highlights": hit.get("highlight", {}).get("content", [])
            } for hit in response["hits"]["hits"]]
        }
        return formatted_results
    except Exception as e:
        # Manejo de errores
        return {"error": str(e)}