from fastapi import FastAPI
from .routes import documents
from fastapi.middleware.cors import CORSMiddleware
from .utils.process_documents.pdf_management.service import ElasticsearchPdfProcessor
from .utils.process_documents.word_management.word import ConvertidorWordPDF
import os

pdf_dir = os.getenv('PDF_DIR', '/app/pdfs')
ruta_salida = os.getenv('RUTA_SALIDA', '/app/pdfsoutput')
  
convertidor = ConvertidorWordPDF(pdf_dir, ruta_salida)
resultados = convertidor.convertir_todos()

processor = ElasticsearchPdfProcessor(pdf_dir)
processor.process_and_index_pdfs()

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

