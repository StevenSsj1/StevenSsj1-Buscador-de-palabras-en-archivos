from datetime import datetime
from typing import Dict, List, Set
from pathlib import Path
import logging
from ..utils.process_documents.pdf_management.service import PDFElasticsearchService

class NewFilesDetector:
    def __init__(self, es_service: PDFElasticsearchService):
        self.es_service = es_service
        self.logger = logging.getLogger('new_files_detector')

    async def get_indexed_files(self) -> Set[str]:
        """Obtiene el conjunto de archivos ya indexados"""
        query = {
            "query": {"match_all": {}},
            "_source": ["relative_path"],
            "size": 10000
        }
        
        response = await self.es_service.es.search(
            index=self.es_service.index_name, 
            body=query
        )
        
        return {
            hit["_source"]["relative_path"] 
            for hit in response["hits"]["hits"]
        }

    def find_new_files(self, indexed_files: Set[str]) -> List[Dict[str, str]]:
        """Encuentra archivos nuevos comparando con los ya indexados"""
        new_files = []
        root_path = Path(self.es_service.root_directory)

        for pdf_path in root_path.rglob('*.pdf'):
            relative_path = self.es_service.get_relative_path(pdf_path, root_path)
            if relative_path not in indexed_files:
                new_files.append({
                    "full_path": str(pdf_path),
                    "relative_path": relative_path
                })

        return new_files

    async def process_new_files(self, new_files: List[Dict[str, str]]) -> Dict:
        """Procesa los archivos nuevos encontrados"""
        results = {
            "processed_files": [],
            "failed_files": [],
            "total_found": len(new_files),
            "total_processed": 0
        }

        for file in new_files:
            try:
                index_result = await self.es_service.index_pdf(  # Agregamos await aquí
                    file["full_path"], 
                    self.es_service.root_directory
                )
                
                if index_result.get("success", False):
                    results["processed_files"].append(file["relative_path"])
                    results["total_processed"] += 1
                else:
                    results["failed_files"].append({
                        "path": file["relative_path"],
                        "error": index_result.get("error")
                    })

            except Exception as e:
                results["failed_files"].append({
                    "path": file["relative_path"],
                    "error": str(e)
                })

        return results
