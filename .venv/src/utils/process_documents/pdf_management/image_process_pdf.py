import os
import logging
from typing import Dict, Optional, List
from pdf2image import convert_from_path
import pytesseract
from pathlib import Path
from datetime import datetime

class ImagePDFProcessor:
    """
    Clase responsable de procesar PDFs que son imágenes y requieren OCR.
    """
    def __init__(self):
        self._processed_files: List[str] = []
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='pdf_processing.log'
        )

    def validate_pdf(self, pdf_path: str) -> bool:
        """
        Valida si el archivo existe y es un PDF válido.
        
        Args:
            pdf_path (str): Ruta al archivo PDF
            
        Returns:
            bool: True si el archivo es válido, False en caso contrario
        """
        try:
            if not os.path.exists(pdf_path):
                logging.error(f"El archivo no existe: {pdf_path}")
                return False
            
            if not pdf_path.lower().endswith('.pdf'):
                logging.error(f"El archivo no es un PDF: {pdf_path}")
                return False

            # Intenta abrir el PDF para verificar que no está corrupto
            with open(pdf_path, 'rb') as file:
                convert_from_path(pdf_path, first_page=0, last_page=1)
            return True
        except Exception as e:
            logging.error(f"Error validando PDF {pdf_path}: {str(e)}")
            return False

    def clean_metadata_value(self, value: Optional[str]) -> str:
        """
        Limpia y formatea valores de metadatos.
        
        Args:
            value (Optional[str]): Valor de metadato a limpiar
            
        Returns:
            str: Valor limpio y formateado
        """
        if not value:
            return "No disponible"
        
        value = str(value).replace('/', '').strip()
        
        if 'D:' in value:
            try:
                date_str = value.replace('D:', '')[:14]
                date_obj = datetime.strptime(date_str, '%Y%m%d%H%M%S')
                return date_obj.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        return value

    def extract_text_from_image_pdf(self, pdf_path: str) -> Dict:
        """
        Extrae texto de un PDF que contiene imágenes usando OCR.
        
        Args:
            pdf_path (str): Ruta al archivo PDF
            
        Returns:
            Dict: Diccionario con toda la información extraída
        """
        info = {
            'metadata': {},
            'pages': {},
            'document_info': {},
            'texto_completo': '',
            'ruta_archivo': str(Path(pdf_path).absolute())
        }

        if not self.validate_pdf(pdf_path):
            info['error'] = "PDF inválido o corrupto"
            return info

        try:
            # Convertir PDF a imágenes
            images = convert_from_path(pdf_path)
            texto_completo = []
            total_palabras = 0
            total_caracteres = 0

            for page_num, image in enumerate(images, 1):
                # Aplicar OCR
                text = pytesseract.image_to_string(image, lang='spa')
                palabras = text.split()
                texto_completo.append(text)

                total_palabras += len(palabras)
                total_caracteres += len(text)

                info['pages'][page_num] = {
                    'texto': text,
                    'numero_caracteres': len(text),
                    'numero_palabras': len(palabras)
                }

            info['texto_completo'] = '\n\n'.join(texto_completo)
            info['document_info'] = {
                'numero_paginas': len(images),
                'tamano_archivo': os.path.getsize(pdf_path),
                'fecha_procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_palabras': total_palabras,
                'total_caracteres': total_caracteres
            }

            self._processed_files.append(pdf_path)
            logging.info(f"PDF procesado exitosamente: {pdf_path}")

        except Exception as e:
            error_msg = f"Error procesando PDF con imágenes: {str(e)}"
            logging.error(error_msg)
            info['error'] = error_msg

        return info