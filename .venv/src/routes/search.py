from fastapi import APIRouter, Query
from typing import Annotated, Optional
from elasticsearch import AsyncElasticsearch
from ..utils.logs.error_handling import CustomLogger, handle_exceptions
from ..service.search_service import SearchService
from ..utils.logs.search_validators import SearchValidator

router = APIRouter(prefix="/api_documents", tags=["api_documents"])
logger = CustomLogger("search_api", "search.log")
client = AsyncElasticsearch([{'host': 'elasticsearch', 'port': 9200, 'scheme': 'http'}])
search_service = SearchService(client, logger)
search_validator = SearchValidator()

@router.get("/search/")
@handle_exceptions(logger)
async def search_documents(
    search_term: Annotated[Optional[str], Query()] = None,
    index_name: Annotated[str, Query()] = "pdfs",
    fuzziness: Annotated[Optional[str], Query()] = "AUTO",
    operator: Annotated[Optional[str], Query()] = "OR",
):
    """Búsqueda fuzzy en documentos."""
    logger.info(
        "Iniciando búsqueda fuzzy",
        {"search_term": search_term, "params": {"fuzziness": fuzziness, "operator": operator}}
    )

    # Validar parámetros
    search_validator.validate_operator(operator)
    search_validator.validate_fuzziness(fuzziness)

    # Construir y ejecutar query
    query = (search_service.build_fuzzy_query(search_term, fuzziness, operator) 
             if search_term else search_service.build_match_all_query())
    
    response = await search_service.execute_search(index_name, query)
    
    # Procesar y retornar resultados
    results = search_service.process_search_results(response, search_term)
    
    logger.info(
        "Búsqueda completada",
        {"total_hits": results["total_hits"]}
    )
    
    return results

@router.get("/search_exact/")
@handle_exceptions(logger)
async def search_exact_documents(
    search_term: Annotated[Optional[str], Query()] = None,
    index_name: Annotated[str, Query()] = "pdfs",
):
    """Búsqueda exacta en documentos."""
    logger.info(
        "Iniciando búsqueda exacta",
        {"search_term": search_term}
    )

    # Construir y ejecutar query
    query = (search_service.build_exact_query(search_term) 
             if search_term else search_service.build_match_all_query())
    
    response = await search_service.execute_search(index_name, query)
    
    # Procesar y retornar resultados
    results = search_service.process_search_results(response, search_term)
    
    logger.info(
        "Búsqueda exacta completada",
        {"total_hits": results["total_hits"]}
    )
    
    return results
