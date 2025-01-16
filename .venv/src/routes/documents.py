from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Annotated, Optional, List
from elasticsearch import AsyncElasticsearch
from datetime import datetime

BASE_URL = "elasticsearch:9200"
client = AsyncElasticsearch(BASE_URL)
router = APIRouter(prefix="/api_documents", tags=["api_documents"])

class ParamsGetDocuments(BaseModel):
    name_index: str = "pdfs"
    id_index: str  # Cambiado a str ya que usamos la ruta relativa como ID

class PageContent(BaseModel):
    page_number: int
    content: str
    highlights: Optional[List[str]] = None

class Document(BaseModel):
    filename: str
    relative_path: str
    total_pages: int
    metadata: dict
    matching_pages: List[PageContent]

async def search_with_term(search_term: str, index_name: str):
    """Busca en el contenido de los documentos usando búsqueda fuzzy."""
    query = {
        "query": {
            "bool": {
                "should": [
                    {
                        "match": {
                            "pages.content": {
                                "query": search_term,
                                "fuzziness": "AUTO"
                            }
                        }
                    },
                    {
                        "match": {
                            "metadata.titulo": {
                                "query": search_term,
                                "boost": 2
                            }
                        }
                    }
                ]
            }
        },
        "_source": ["filename", "relative_path", "total_pages", "metadata", "pages"],
        "highlight": {
            "fields": {
                "pages.content": {
                    "number_of_fragments": 3,
                    "fragment_size": 150
                }
            }
        }
    }

    try:
        response = await client.search(index=index_name, body=query)

        formatted_results = {
            "total_hits": response["hits"]["total"]["value"],
            "results": []
        }

        for hit in response["hits"]["hits"]:
            doc_result = {
                "filename": hit["_source"]["filename"],
                "relative_path": hit["_source"]["relative_path"],
                "total_pages": hit["_source"]["total_pages"],
                "metadata": hit["_source"]["metadata"],
                "matching_pages": []
            }

            # Si el documento tiene páginas
            if "pages" in hit["_source"]:
                # Buscar en todas las páginas del documento
                for page in hit["_source"]["pages"]:
                    # Verificar si el término de búsqueda está en el contenido de la página
                    # Usando una comparación más flexible para búsqueda fuzzy
                    if any(word in page["content"].lower() for word in search_term.lower().split()):
                        highlights = []
                        if "highlight" in hit:
                            highlights = hit["highlight"].get("pages.content", [])

                        doc_result["matching_pages"].append({
                            "page_number": page["number"],
                            "content": page["content"],
                            "highlights": highlights
                        })

            formatted_results["results"].append(doc_result)

        return formatted_results
    except Exception as e:
        return {"error": str(e)}
    
async def search_without_term(index_name: str):
    """Devuelve todos los documentos sin buscar coincidencias en el contenido."""
    query = {
        "query": {
            "match_all": {}
        },
        "_source": ["filename", "relative_path", "total_pages", "pages"]
    }

    response = await client.search(index=index_name, body=query)

    formatted_results = {
        "total_hits": response["hits"]["total"]["value"],
        "results": []
    }

    for hit in response["hits"]["hits"]:
        doc_result = {
            "filename": hit["_source"]["filename"],
            "relative_path": hit["_source"]["relative_path"],
            "total_pages": hit["_source"]["total_pages"],
            "matching_pages": []
        }

        # Solo incluir la primera página
        if hit["_source"]["pages"]:
            first_page = hit["_source"]["pages"][0]
            doc_result["matching_pages"].append({
                "page_number": first_page["number"],
                "content": first_page["content"]
            })

        formatted_results["results"].append(doc_result)

    return formatted_results

@router.get("/documents/")
async def get_all_documents():
    """Obtiene todos los documentos PDF indexados."""
    query = {
        "query": {"match_all": {}},
        "_source": ["filename", "relative_path", "total_pages", "pages"]
    }
    
    result = await client.search(
        index="pdfs",
        body=query
    )
    
    formatted_results = {
        "total_hits": result["hits"]["total"]["value"],
        "documents": [{
            "filename": hit["_source"]["filename"],
            "relative_path": hit["_source"]["relative_path"],
            "total_pages": hit["_source"]["total_pages"],
            "metadata": hit["_source"]["pages"]
        } for hit in result["hits"]["hits"]]
    }
    
    return formatted_results

@router.get("/document/")
async def get_document_by_index(params_documents: Annotated[ParamsGetDocuments, Query()]):
    """Obtiene un documento específico por su ID (ruta relativa)."""
    try:
        resp = await client.get(index=params_documents.name_index, id=params_documents.id_index)
        return {
            "filename": resp["_source"]["filename"],
            "relative_path": resp["_source"]["relative_path"],
            "total_pages": resp["_source"]["total_pages"],
            "metadata": resp["_source"]["metadata"],
            "pages": resp["_source"]["pages"]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/search/")
async def search_documents(
    search_term: Annotated[Optional[str], Query()] = None,
    index_name: Annotated[str, Query()] = "pdfs",
):
    try:
        if search_term:
            return await search_with_term(search_term, index_name)
        else:
            return await search_without_term(index_name)
    except Exception as e:
        return {"error": str(e)}
    
    
@router.get("/search_exact/")
async def search_exact_documents(
    search_term: Annotated[Optional[str], Query()] = None,
    index_name: Annotated[str, Query()] = "pdfs",
):
    """Busca en el contenido de los documentos usando búsqueda exacta."""
    if search_term:
        query = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match_phrase": {
                                "pages.content": search_term
                            }
                        },
                        {
                            "match_phrase": {
                                "metadata.titulo": search_term
                            }
                        }
                    ]
                }
            },
            "_source": ["filename", "relative_path", "total_pages", "metadata", "pages"],
            "highlight": {
                "fields": {
                    "pages.content": {
                        "number_of_fragments": 3,
                        "fragment_size": 150
                    }
                }
            }
        }
    else:
        query = {
            "query": {"match_all": {}},
            "_source": ["filename", "relative_path", "total_pages", "metadata"]
        }
    try:
        response = await client.search(index=index_name, body=query)
        
        formatted_results = {
            "total_hits": response["hits"]["total"]["value"],
            "results": []
        }
        
        for hit in response["hits"]["hits"]:
            doc_result = {
                "filename": hit["_source"]["filename"],
                "relative_path": hit["_source"]["relative_path"],
                "total_pages": hit["_source"]["total_pages"],
                "metadata": hit["_source"]["metadata"],
                "matching_pages": []
            }
            
            # Si hay búsqueda y el documento tiene páginas
            if search_term and "pages" in hit["_source"]:
                # Buscar en todas las páginas del documento
                for page in hit["_source"]["pages"]:
                    if search_term.lower() in page["content"].lower():
                        # Obtener los highlights si existen
                        highlights = []
                        if "highlight" in hit:
                            highlights = hit["highlight"].get("pages.content", [])
                        
                        doc_result["matching_pages"].append({
                            "page_number": page["number"],
                            "content": page["content"],
                            "highlights": highlights
                        })
            
            formatted_results["results"].append(doc_result)
            
        return formatted_results
    except Exception as e:
        return {"error": str(e)}