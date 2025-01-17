from spire.doc import *
from pathlib import Path
from spire.doc.common import *


class ConvertidorWordPDF:
    def __init__(self, ruta_base, ruta_salida):
        self.ruta_base = Path(ruta_base)
        self.ruta_salida = Path(ruta_salida)
        self.ruta_salida.mkdir(parents=True, exist_ok=True)

    def convertir_archivo(self, archivo_word):
        try:
            # Definir el nombre del archivo de salida
            ruta_pdf = self.ruta_salida / archivo_word.with_suffix('.pdf').name
            
            # Crear documento y cargar el archivo Word
            document = Document()
            document.LoadFromFile(str(archivo_word))

            # Guardar el archivo PDF
            document.SaveToFile(str(ruta_pdf), FileFormat.PDF)
            document.Close()

            return True, f"Convertido: {ruta_pdf}"

        except Exception as e:
            return False, f"Error en '{archivo_word}': {str(e)}"

    def convertir_todos(self):
        archivos = list(self.ruta_base.rglob("*.docx"))
        resultados = [self.convertir_archivo(archivo) for archivo in archivos]
        return resultados

