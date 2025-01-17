from fastapi import APIRouter, Query, status
from pydantic import BaseModel
from typing import Annotated, Optional, List
from elasticsearch import AsyncElasticsearch
from ..utils.logs.error_handling import CustomLogger, handle_exceptions, AppException
from ..service.check_new_files import NewFilesDetector
from ..utils.process_documents.pdf_management.service import PDFElasticsearchService
import os 

logger = CustomLogger("documents_api", "documents_api.log")
BASE_URL = "elasticsearch:9200"
PDF_DIR = os.getenv('PDF_DIR', '/app/pdfs')

client = AsyncElasticsearch(BASE_URL)
router = APIRouter(prefix="/api_documents", tags=["api_documents"])

# Inicialización de servicios
es_service = PDFElasticsearchService(
    es_host='elasticsearch',
    es_port=9200,
    index_name='pdfs',
    root_directory=PDF_DIR,
    max_workers=4
)
files_detector = NewFilesDetector(es_service)


class ParamsGetDocuments(BaseModel):
    name_index: str = "pdfs"
    id_index: str  

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

@router.post("/check_new_files/")
@handle_exceptions(logger)
async def check_new_files():
    """
    Detecta y procesa archivos nuevos en el directorio configurado.
    """
    try:
        logger.info(
            "Iniciando detección de archivos nuevos",
            {
                "timestamp_utc": "2025-01-17 03:48:20",
                "user": "StevenSsj1"
            }
        )

        # Obtener archivos indexados
        indexed_files = await files_detector.get_indexed_files()
        
        # Encontrar archivos nuevos
        new_files = files_detector.find_new_files(indexed_files)
        
        logger.info(
            "Archivos nuevos encontrados",
            {
                "timestamp_utc": "2025-01-17 03:48:20",
                "user": "StevenSsj1",
                "new_files_count": len(new_files)
            }
        )

        if not new_files:
            return {
                "status": "success",
                "message": "No se encontraron archivos nuevos",
                "total_found": 0,
                "total_processed": 0
            }

        # Procesar archivos nuevos
        results = await files_detector.process_new_files(new_files)

        # Forzar refresh del índice
        await es_service.es.indices.refresh(index=es_service.index_name)

        logger.info(
            "Proceso de detección completado",
            {
                "timestamp_utc": "2025-01-17 03:48:20",
                "user": "StevenSsj1",
                "total_found": results["total_found"],
                "total_processed": results["total_processed"]
            }
        )

        return {
            "status": "success",
            **results
        }

    except Exception as e:
        logger.error(
            "Error en la detección de archivos nuevos",
            {
                "timestamp_utc": "2025-01-17 03:48:20",
                "user": "StevenSsj1",
                "error": str(e)
            }
        )
        raise AppException(
            message="Error en la detección de archivos nuevos",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            extra={"error": str(e)}
        )