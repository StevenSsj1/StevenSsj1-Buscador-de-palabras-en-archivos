from elasticsearch import AsyncElasticsearch  # Cambiamos la importación
from typing import Dict, List, Optional
import logging
from datetime import datetime
import os
from pathlib import Path
from .pdf_manager import PDFManager
from concurrent.futures import ThreadPoolExecutor

class PDFElasticsearchService:
    def __init__(
        self, 
        es_host: str = 'localhost',
        es_port: int = 9200,
        index_name: str = 'pdfs',
        root_directory: str = None,
        max_workers: int = 4
    ):
        # Usamos AsyncElasticsearch en lugar de Elasticsearch
        self.es = AsyncElasticsearch([{'host': es_host, 'port': es_port, 'scheme': 'http'}])
        self.index_name = index_name
        self.root_directory = root_directory
        self.pdf_manager = PDFManager(root_directory, max_workers) if root_directory else None
        self.max_workers = max_workers
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='elasticsearch_pdf_service.log'
        )

    async def setup_index(self):
        if not await self.es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "filename": {"type": "keyword"},
                        "file_path": {"type": "keyword"},
                        "relative_path": {"type": "keyword"},
                        "pages": {
                            "type": "nested",
                            "properties": {
                                "number": {"type": "integer"},
                                "content": {"type": "text", "analyzer": "standard"},
                                "is_image": {"type": "boolean"},
                                "confidence": {"type": "float"}
                            }
                        },
                        "total_pages": {"type": "integer"},
                        "metadata": {
                            "properties": {
                                "autor": {"type": "text"},
                                "titulo": {"type": "text"},
                                "fecha_creacion": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"}
                            }
                        },
                        "document_info": {
                            "properties": {
                                "tamano_archivo": {"type": "long"},
                                "fecha_procesamiento": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
                                "tipo_procesamiento": {"type": "keyword"}
                            }
                        },
                        "indexed_date": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
                        "directory_structure": {"type": "keyword"}
                    }
                }
            }
            self.es.indices.create(index=self.index_name, body=mapping)
            logging.info(f"Índice '{self.index_name}' creado con éxito")

    def find_pdf_files(self, root_dir: str) -> List[Path]:
        pdf_files = []
        root_path = Path(root_dir)
        
        try:
            for path in root_path.rglob('*.pdf'):
                if path.is_file():
                    pdf_files.append(path)
            
            logging.info(f"Encontrados {len(pdf_files)} archivos PDF en {root_dir}")
            return pdf_files
        except Exception as e:
            logging.error(f"Error buscando PDFs en {root_dir}: {str(e)}")
            return []

    def get_relative_path(self, file_path: Path, root_dir: Path) -> str:
        try:
            return str(file_path.relative_to(root_dir))
        except ValueError:
            return str(file_path)

    async def index_pdf(self, pdf_path: str, root_dir: Optional[str] = None) -> Dict:
        try:
            # Usar PDFManager para procesar el PDF
            if self.pdf_manager is None:
                self.pdf_manager = PDFManager(root_dir or os.path.dirname(pdf_path))
            
            pdf_info = self.pdf_manager.process_pdf(pdf_path)
            
            if 'error' in pdf_info:
                logging.error(f"Error procesando PDF {pdf_path}: {pdf_info['error']}")
                return {"success": False, "error": pdf_info['error']}

            path_obj = Path(pdf_path)
            root_path = Path(root_dir) if root_dir else path_obj.parent
            relative_path = str(path_obj.relative_to(root_path))
            directory_structure = str(path_obj.parent)

            # Crear estructura de páginas
            pages = []
            for page_num, page_data in pdf_info['pages'].items():
                page_info = {
                    "number": page_num,
                    "content": page_data['texto'],
                    "is_image": page_data.get('is_image', False),
                    "confidence": page_data.get('confidence', 1.0)
                }
                pages.append(page_info)

            # Crear documento para Elasticsearch
            document = {
                "filename": path_obj.name,
                "file_path": str(path_obj.absolute()),
                "relative_path": relative_path,
                "directory_structure": directory_structure,
                "pages": pages,
                "total_pages": pdf_info['document_info']['numero_paginas'],
                "metadata": pdf_info['metadata'],
                "document_info": {
                    **pdf_info['document_info'],
                    "tipo_procesamiento": "OCR" if any(p.get('is_image', False) for p in pages) else "texto"
                },
                "indexed_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Usar la ruta relativa como ID único del documento
            doc_id = relative_path
            
            await self.es.index(
                index=self.index_name,
                id=doc_id,
                document=document
            )
            
            logging.info(f"PDF indexado exitosamente: {pdf_path}")
            return {
                "success": True,
                "message": f"PDF indexado exitosamente con {len(pages)} páginas",
                "indexed_pages": len(pages),
                "processing_type": document["document_info"]["tipo_procesamiento"]
            }

        except Exception as e:
            error_msg = f"Error indexando PDF {pdf_path}: {str(e)}"
            logging.error(error_msg)
            return {"success": False, "error": error_msg}
        
    def process_directory(self, directory_path: str, parallel: bool = True) -> Dict:
        try:
            pdf_files = self.find_pdf_files(directory_path)
            total_files = len(pdf_files)
            
            if total_files == 0:
                return {"message": "No se encontraron archivos PDF", "processed": 0}

            results = {
                "total_files": total_files,
                "successful": 0,
                "failed": 0,
                "errors": []
            }

            logging.info(f"Iniciando procesamiento de {total_files} archivos PDF")

            if parallel and total_files > 1:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = []
                    for pdf_path in pdf_files:
                        futures.append(executor.submit(self.index_pdf, str(pdf_path), directory_path))
                    
                    for i, future in enumerate(futures):
                        result = future.result()
                        if result.get("success", False):
                            results["successful"] += 1
                        else:
                            results["failed"] += 1
                            results["errors"].append(result.get("error"))
                        
                        logging.info(f"Progreso: {i + 1}/{total_files} archivos procesados")
            else:
                for i, pdf_path in enumerate(pdf_files):
                    result = self.index_pdf(str(pdf_path), directory_path)
                    if result.get("success", False):
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(result.get("error"))
                    
                    logging.info(f"Progreso: {i + 1}/{total_files} archivos procesados")

            logging.info(f"Procesamiento de directorio completado: {results}")
            return results

        except Exception as e:
            error_msg = f"Error procesando directorio {directory_path}: {str(e)}"
            logging.error(error_msg)
            return {"error": error_msg}