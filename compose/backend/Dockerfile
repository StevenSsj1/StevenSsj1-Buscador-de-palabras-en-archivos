FROM python:3.12-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-spa \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# Crear directorios de trabajo
WORKDIR /app
RUN mkdir -p /app/pdfs /app/output
RUN pip install --upgrade pip

# Copiar requirements primero
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY backend/ .

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]