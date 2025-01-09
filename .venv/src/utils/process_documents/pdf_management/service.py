from .pdf_manager import PDFManager
from elasticsearch import Elasticsearch
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class ElasticsearchPdfProcessor:
    def __init__(self, pdf_dir: str, es_host='elasticsearch', es_port=9200, max_workers=4):
        self.pdf_manager = PDFManager(pdf_dir, max_workers=max_workers)
        self.es_client = Elasticsearch([{'host': es_host, 'port': es_port, 'scheme': 'http'}])
        self.max_workers = max_workers

    def index_batch(self, documents: List[Dict], index_name: str) -> int:
        try:
            operations = []
            for doc in documents:
                operations.extend([
                    {"index": {"_index": index_name}},
                    doc
                ])
            
            if operations:
                response = self.es_client.bulk(operations)
                return len(documents) if not response['errors'] else 0
            return 0
        except Exception as e:
            logging.error(f"Error en indexación bulk: {str(e)}")
            return 0

    def process_and_index_pdfs(self, index_name='pdfs', batch_size=100):
        results = self.pdf_manager.process_all_pdfs()
        documents_batch = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for filename, info in results.items():
                if 'error' in info:
                    continue
                    
                pdf_info = info['info']
                for page_num, page_info in pdf_info['pages'].items():
                    if page_info.get('texto'):
                        doc = {
                            'name_document': filename,
                            'page_number': int(page_num),
                            'content': page_info['texto'].strip(),
                            'total_pages': len(pdf_info['pages']),
                            'processed_date': datetime.now().isoformat()
                        }
                        documents_batch.append(doc)
                        
                        if len(documents_batch) >= batch_size:
                            batch_to_index = documents_batch.copy()
                            documents_batch = []
                            futures.append(
                                executor.submit(self.index_batch, batch_to_index, index_name)
                            )
            
            if documents_batch:
                futures.append(
                    executor.submit(self.index_batch, documents_batch, index_name)
                )
            
            total_indexed = sum(future.result() for future in as_completed(futures))
            logging.info(f"Total de documentos indexados: {total_indexed}")

