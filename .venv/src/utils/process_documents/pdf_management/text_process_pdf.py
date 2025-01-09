import os
from PyPDF2 import PdfReader
import logging
from typing import Dict

class TextPDFProcessor:
    """
    Clase responsable de procesar PDFs que contienen texto directamente extraíble.
    """
    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='pdf_processing.log'
        )

    def extract_text_from_pdf(self, pdf_path: str) -> Dict:
        """
        Extrae texto e información de un PDF que contiene texto directamente extraíble.
        """
        info = {
            'metadata': {},
            'pages': {},
            'document_info': {},
            'texto_completo': ''
        }

        try:
            reader = PdfReader(pdf_path)
            texto_completo = []

            # Extraer metadatos
            if reader.metadata:
                info['metadata'] = {
                    'autor': reader.metadata.get('/Author', 'No disponible'),
                    'creador': reader.metadata.get('/Creator', 'No disponible'),
                    'productor': reader.metadata.get('/Producer', 'No disponible'),
                    'fecha_creacion': reader.metadata.get('/CreationDate', 'No disponible'),
                    'fecha_modificacion': reader.metadata.get('/ModDate', 'No disponible'),
                    'titulo': reader.metadata.get('/Title', 'No disponible')
                }

            info['document_info'] = {
                'numero_paginas': len(reader.pages),
                'tamano_archivo': os.path.getsize(pdf_path)
            }

            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                texto_completo.append(text)

                info['pages'][page_num] = {
                    'texto': text,
                    'rotacion': page.get('/Rotate', 0) % 360,
                    'numero_caracteres': len(text),
                    'numero_palabras': len(text.split())
                }

            info['texto_completo'] = '\n\n'.join(texto_completo)

        except Exception as e:
            error_msg = f"Error procesando PDF con texto: {str(e)}"
            logging.error(error_msg)
            info['error'] = error_msg

        return info