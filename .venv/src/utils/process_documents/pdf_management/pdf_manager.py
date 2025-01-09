import os
import logging
from datetime import datetime
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .text_process_pdf import TextPDFProcessor
from .image_process_pdf import ImagePDFProcessor

class PDFManager:
    """
    Clase principal que coordina el procesamiento de PDFs, delegando a los procesadores específicos.
    """
    def __init__(self, root_directory: str, max_workers: int = 4):
        self.root_directory = root_directory
        self.output_directory = os.path.join(root_directory, "corregidos")
        self.text_processor = TextPDFProcessor()
        self.image_processor = ImagePDFProcessor()
        self.max_workers = max_workers
        self.setup_logging()
        self.ensure_output_directory()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='pdf_processing.log'
        )

    def ensure_output_directory(self):
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)
            logging.info(f"Creado directorio de salida: {self.output_directory}")

    def get_pdf_files(self) -> List[str]:
        pdf_files = []
        for root, _, files in os.walk(self.root_directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        return pdf_files

    def _generate_output_filename(self, original_path: str) -> str:
        rel_path = os.path.relpath(original_path, self.root_directory)
        dir_path = os.path.dirname(rel_path)
        base_name = os.path.basename(original_path)
        name_without_ext = os.path.splitext(base_name)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{name_without_ext}_corregido_{timestamp}.pdf"

        output_dir = os.path.join(self.output_directory, dir_path)
        os.makedirs(output_dir, exist_ok=True)

        return os.path.join(output_dir, new_filename)
    def process_pdf(self, pdf_path: str) -> Dict:
        """
        Procesa un PDF, determinando si es texto o imagen y usando el procesador apropiado.
        """
        try:
            # Intentar primero con el procesador de texto
            info = self.text_processor.extract_text_from_pdf(pdf_path)
            
            # Si no se encontró texto en ninguna página, usar el procesador de imágenes
            if all(not page_info['texto'].strip() for page_info in info['pages'].values()):
                info = self.image_processor.extract_text_from_image_pdf(pdf_path)

            return info

        except Exception as e:
            error_msg = f"Error procesando {pdf_path}: {str(e)}"
            logging.error(error_msg)
            return {'error': error_msg}

    def process_all_pdfs(self) -> Dict[str, Dict]:
        """
        Procesa todos los PDFs en el directorio.
        """
        results = {}

        for pdf_path in self.get_pdf_files():
            try:
                filename = os.path.basename(pdf_path)
                logging.info(f"Procesando: {filename}")

                # Procesar el PDF
                pdf_info = self.process_pdf(pdf_path)

                results[filename] = {
                    'info': pdf_info
                }

                logging.info(f"Completado procesamiento de: {filename}")

            except Exception as e:
                logging.error(f"Error en archivo {filename}: {str(e)}")
                results[filename] = {'error': str(e)}

        return results

    def process_single_pdf(self, pdf_path: str) -> Tuple[str, Dict]:
        filename = os.path.basename(pdf_path)
        try:
            logging.info(f"Procesando: {filename}")
            pdf_info = self.process_pdf(pdf_path)
            return filename, {'info': pdf_info}
        except Exception as e:
            logging.error(f"Error en archivo {filename}: {str(e)}")
            return filename, {'error': str(e)}

        except Exception as e:
            error_msg = f"Error procesando {pdf_path}: {str(e)}"
            logging.error(error_msg)
            return {'error': error_msg}

    def process_all_pdfs(self) -> Dict[str, Dict]:
        pdf_files = self.get_pdf_files()
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.process_single_pdf, pdf_path): pdf_path 
                for pdf_path in pdf_files
            }
            
            for future in as_completed(future_to_file):
                filename, result = future.result()
                results[filename] = result
                
        return results