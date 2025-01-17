from fastapi import FastAPI
from .routes import documents, search
from fastapi.middleware.cors import CORSMiddleware
from .utils.process_documents.pdf_management.service import PDFElasticsearchService
from .utils.process_documents.word_management.word import ConvertidorWordPDF
import os

pdf_dir = os.getenv('PDF_DIR', '/app/pdfs')
ruta_salida = os.getenv('RUTA_SALIDA', '/app/pdfsoutput')
  
convertidor = ConvertidorWordPDF(pdf_dir, ruta_salida)
resultados = convertidor.convertir_todos()

pdf_service = PDFElasticsearchService(
    es_host='elasticsearch',
    es_port=9200,

)

result = pdf_service.process_directory(pdf_dir)

app = FastAPI(
    title="Documents Processing API",
    description="API para procesar y búsqueda de documentos",
    version="1.0.0"
)

origin = [
    "http://localhost:4200",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(documents.router)
app.include_router(search.router)

