import os
from PyPDF2 import PdfReader
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

class TextPDFProcessor:
    """
    Clase responsable de procesar PDFs que contienen texto directamente extraíble.
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
                PdfReader(file)
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
        
        # Elimina caracteres especiales comunes en metadatos PDF
        value = str(value).replace('/', '').strip()
        
        # Intenta convertir fechas en formato PDF a formato legible
        if 'D:' in value:
            try:
                # Formato común de fecha en PDFs: D:20240112235959
                date_str = value.replace('D:', '')[:14]
                date_obj = datetime.strptime(date_str, '%Y%m%d%H%M%S')
                return date_obj.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        return value
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict:
        """
        Extrae texto e información detallada de un PDF.
        
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
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                texto_completo = []
                total_palabras = 0
                total_caracteres = 0

                # Extraer metadatos con limpieza
                if reader.metadata:
                    info['metadata'] = {
                        'autor': self.clean_metadata_value(reader.metadata.get('/Author')),
                        'fecha_creacion': self.clean_metadata_value(reader.metadata.get('/CreationDate')),
                        'titulo': self.clean_metadata_value(reader.metadata.get('/Title')),
                    }

                # Procesar páginas
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    palabras = text.split()
                    texto_completo.append(text)
                    
                    total_palabras += len(palabras)
                    total_caracteres += len(text)

                    info['pages'][page_num] = {
                        'texto': text,
                    }

                # Información del documento
                texto_completo_str = '\n\n'.join(texto_completo)
                info['document_info'] = {
                    'numero_paginas': len(reader.pages),
                    'tamano_archivo': os.path.getsize(pdf_path),
                    'fecha_procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                info['texto_completo'] = texto_completo_str
                self._processed_files.append(pdf_path)
                
                logging.info(f"PDF procesado exitosamente: {pdf_path}")
                
        except Exception as e:
            error_msg = f"Error procesando PDF: {str(e)}"
            logging.error(error_msg)
            info['error'] = error_msg

        return info
