from elasticsearch import Elasticsearch
from typing import Dict, List, Optional
import logging
from datetime import datetime
import os
from pathlib import Path
from .text_process_pdf import TextPDFProcessor
from concurrent.futures import ThreadPoolExecutor

class PDFElasticsearchService:
    def __init__(
        self, 
        es_host: str = 'localhost',
        es_port: int = 9200,
        index_name: str = 'pdfs',
        pdf_processor: Optional[TextPDFProcessor] = None,
        max_workers: int = 4
    ):
        self.es = Elasticsearch([{'host': es_host, 'port': es_port, 'scheme': 'http'}])
        self.index_name = index_name
        self.pdf_processor = pdf_processor or TextPDFProcessor()
        self.max_workers = max_workers
        self.setup_logging()
        self.setup_index()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='elasticsearch_pdf_service.log'
        )

    def setup_index(self):
        if not self.es.indices.exists(index=self.index_name):
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
                                "content": {"type": "text", "analyzer": "standard"}
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
                                "fecha_procesamiento": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"}
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

    def index_pdf(self, pdf_path: str, root_dir: Optional[str] = None) -> Dict:
        try:
            pdf_info = self.pdf_processor.extract_text_from_pdf(pdf_path)
            
            if 'error' in pdf_info:
                logging.error(f"Error procesando PDF {pdf_path}: {pdf_info['error']}")
                return {"success": False, "error": pdf_info['error']}

            path_obj = Path(pdf_path)
            root_path = Path(root_dir) if root_dir else path_obj.parent
            relative_path = self.get_relative_path(path_obj, root_path)
            directory_structure = str(path_obj.parent)

            # Crear estructura de páginas
            pages = []
            for page_num, page_data in pdf_info['pages'].items():
                pages.append({
                    "number": page_num,
                    "content": page_data['texto']
                })

            # Crear un único documento para todo el PDF
            document = {
                "filename": path_obj.name,
                "file_path": str(path_obj.absolute()),
                "relative_path": relative_path,
                "directory_structure": directory_structure,
                "pages": pages,
                "total_pages": pdf_info['document_info']['numero_paginas'],
                "metadata": pdf_info['metadata'],
                "document_info": pdf_info['document_info'],
                "indexed_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Usar la ruta relativa como ID único del documento
            doc_id = relative_path
            
            self.es.index(
                index=self.index_name,
                id=doc_id,
                document=document
            )
            
            logging.info(f"PDF indexado exitosamente: {pdf_path}")
            return {
                "success": True,
                "message": f"PDF indexado exitosamente con {len(pages)} páginas",
                "indexed_pages": len(pages)
            }

        except Exception as e:
            error_msg = f"Error indexando PDF {pdf_path}: {str(e)}"
            logging.error(error_msg)
            return {"success": False, "error": error_msg}

    def search_pdfs(
        self, 
        query: str, 
        directory: Optional[str] = None,
        fields: List[str] = None,
        size: int = 10
    ) -> Dict:
        try:
            if fields is None:
                fields = ['pages.content', 'metadata.titulo', 'metadata.autor']

            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "nested": {
                                    "path": "pages",
                                    "query": {
                                        "match": {
                                            "pages.content": query
                                        }
                                    },
                                    "inner_hits": {
                                        "highlight": {
                                            "fields": {
                                                "pages.content": {}
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": size
            }

            if directory:
                search_body["query"]["bool"]["filter"] = {
                    "prefix": {
                        "directory_structure": str(Path(directory).absolute())
                    }
                }
            
            response = self.es.search(index=self.index_name, body=search_body)
            
            results = {
                "total_hits": response["hits"]["total"]["value"],
                "results": []
            }
            
            for hit in response["hits"]["hits"]:
                # Obtener las páginas que coinciden con la búsqueda
                matching_pages = []
                if "inner_hits" in hit:
                    for inner_hit in hit["inner_hits"]["pages"]["hits"]["hits"]:
                        page_number = inner_hit["_source"]["number"]
                        highlights = inner_hit.get("highlight", {}).get("pages.content", [])
                        matching_pages.append({
                            "page_number": page_number,
                            "highlights": highlights
                        })

                result = {
                    "filename": hit["_source"]["filename"],
                    "relative_path": hit["_source"]["relative_path"],
                    "total_pages": hit["_source"]["total_pages"],
                    "score": hit["_score"],
                    "matching_pages": matching_pages,
                    "metadata": hit["_source"]["metadata"]
                }
                results["results"].append(result)
            
            return results

        except Exception as e:
            error_msg = f"Error en la búsqueda: {str(e)}"
            logging.error(error_msg)
            return {"error": error_msg}

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