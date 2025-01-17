from fastapi import FastAPI
from .routes import documents, search
from fastapi.middleware.cors import CORSMiddleware
from .utils.process_documents.pdf_management.service import PDFElasticsearchService
from .utils.process_documents.word_management.word import ConvertidorWordPDF
import os
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables de entorno
pdf_dir = os.getenv('PDF_DIR', '/app/pdfs')
ruta_salida = os.getenv('RUTA_SALIDA', '/app/pdfsoutput')

# Inicialización del servicio de Elasticsearch
pdf_service = PDFElasticsearchService(
    es_host='elasticsearch',
    es_port=9200,
)

app = FastAPI(
    title="Documents Processing API",
    description="API para procesar y búsqueda de documentos",
    version="1.0.0"
)

# Configuración CORS
origins = [
    "http://localhost:4200",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

async def initialize_documents():
    """
    Función para inicializar el procesamiento de documentos
    """
    try:
        # Primero convertimos los documentos Word a PDF
        logger.info("Iniciando conversión de documentos Word a PDF...")
        convertidor = ConvertidorWordPDF(pdf_dir, ruta_salida)
        resultados_conversion = convertidor.convertir_todos()
        logger.info(f"Resultados de conversión: {resultados_conversion}")

        # Luego procesamos los PDFs con Elasticsearch
        logger.info("Iniciando indexación de documentos en Elasticsearch...")
        
        # Configurar el índice
        await pdf_service.setup_index()
        # Procesar el directorio
        result = await pdf_service.process_directory(pdf_dir)
        logger.info(f"Resultados de indexación: {result}")
        return result
    except Exception as e:
        logger.error(f"Error en la inicialización de documentos: {str(e)}")
        return {"error": str(e)}

@app.on_event("startup")
async def startup_event():
    """
    Evento que se ejecuta al iniciar la aplicación
    """
    logger.info("Iniciando la aplicación y el procesamiento de documentos...")
    await initialize_documents()

@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento que se ejecuta al cerrar la aplicación
    """
    try:
        await pdf_service.close()
        logger.info("Conexión con Elasticsearch cerrada correctamente")
    except Exception as e:
        logger.error(f"Error cerrando la conexión con Elasticsearch: {str(e)}")

# Incluir los routers existentes
app.include_router(documents.router)
app.include_router(search.router)