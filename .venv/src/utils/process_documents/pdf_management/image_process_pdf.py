import os
import logging
from typing import Dict
from pdf2image import convert_from_path
import pytesseract

class ImagePDFProcessor:
    """
    Clase responsable de procesar PDFs que son imágenes y requieren OCR.
    """
    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='pdf_processing.log'
        )

    def extract_text_from_image_pdf(self, pdf_path: str) -> Dict:
        """
        Extrae texto de un PDF que contiene imágenes usando OCR.
        """
        info = {
            'metadata': {},
            'pages': {},
            'document_info': {},
            'texto_completo': ''
        }

        try:
            # Convertir PDF a imágenes
            images = convert_from_path(pdf_path)
            texto_completo = []

            for page_num, image in enumerate(images, 1):
                # Aplicar OCR
                text = pytesseract.image_to_string(image, lang='spa')
                texto_completo.append(text)

                info['pages'][page_num] = {
                    'texto': text,
                    'numero_caracteres': len(text),
                    'numero_palabras': len(text.split())
                }

            info['texto_completo'] = '\n\n'.join(texto_completo)
            info['document_info'] = {
                'numero_paginas': len(images),
                'tamano_archivo': os.path.getsize(pdf_path)
            }

        except Exception as e:
            error_msg = f"Error procesando PDF con imágenes: {str(e)}"
            logging.error(error_msg)
            info['error'] = error_msg

        return info
