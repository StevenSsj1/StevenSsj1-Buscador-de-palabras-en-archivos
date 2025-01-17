```markdown
# Procesador de PDF con Elasticsearch

## 📋 Descripción
Aplicación web que procesa documentos PDF utilizando Elasticsearch para indexación y capacidades de búsqueda. El sistema consta de un procesador PDF backend, una interfaz web frontend y una instancia de Elasticsearch para almacenamiento y búsqueda de documentos.

## 🏗️ Arquitectura
El proyecto está construido usando una arquitectura de microservicios con tres componentes principales:
- Frontend (Angular)
- Backend (Procesador PDF)
- Elasticsearch

## 🔧 Tecnologías Utilizadas
- **Frontend**: Angular
- **Backend**: Python
- **Motor de Búsqueda**: Elasticsearch 8.17.0
- **Plataforma de Contenedores**: Docker y Docker Compose
- **Servidor Web**: Nginx

## 📁 Estructura del Proyecto

proyecto/
├── envs/
│   ├── elasticsearch.env
│   └── pdf-processor.env
├── compose/
│   ├── frontend/
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   ├── backend/
│   │   └── Dockerfile
│   └── docker-compose.yml
├── frontend/
│   ├── src/
│   ├── package.json
│   └── angular.json
├── backend/
│   └── requirements.txt


## 🚀 Instalación y Configuración

### Requisitos Previos
- Docker
- Docker Compose
- Git

### Configuración del Entorno


1. Clonar el repositorio:
```
bash
git clone <url-del-repositorio>
cd <directorio-del-proyecto>

```
DESPUES DE CLONAR EL REPOSITORIO SE NECESITARA UNA CARPETA EN DONDE ESTAN LOS DOCUMENTOS QUE SE INDEXARAN, Y LUEGO PONER SU UBICACION EN EL .env, DEL DIRECTORIO COMPOSE

2. Configurar variables de entorno:
Crear `envs/elasticsearch.env`:
```env
discovery.type=single-node
xpack.security.enabled=false
ES_JAVA_OPTS=-Xms512m -Xmx512m
bootstrap.memory_lock=true
```

Crear `envs/pdf-processor.env`:
```env
PDF_DIR=/app/pdfs
RUTA_SALIDA=/app/pdfsoutput
PYTHONUNBUFFERED=1
ES_HOST=elasticsearch
ES_PORT=9200
```

### Ejecutar la Aplicación
1. Iniciar los servicios:
```bash
cd compose
docker-compose up --build
```

2. Acceder a las aplicaciones:
- Frontend: http://localhost:80
- Elasticsearch: http://localhost:9200
- Procesador PDF: http://localhost:8000

## 🌐 Configuración de Red
La aplicación utiliza una red Docker personalizada con la siguiente configuración:
- Nombre de la Red: elastic_network
- Subred: 192.168.5.0/24
- Asignación de IPs:
  - Elasticsearch: Dinámica
  - Procesador PDF: 192.168.5.3
  - Aplicación Web: 192.168.5.4

## 📚 Uso
1. Colocar archivos PDF en un direcotirio puede ser`pdfs/`, la ruta de este tendra que ser usa en el .env que se encuentra en el directorio compose.
2. El sistema procesará automáticamente los PDFs y los almacenará en Elasticsearch
3. Acceder a la interfaz web para buscar y ver documentos procesados
4. Los archivos procesados estarán disponibles en el directorio `pdfsoutput/`

## 🔍 Características
- Procesamiento de documentos PDF
- Capacidades de búsqueda de texto completo
- Interfaz de usuario web
- Extracción de metadatos de documentos
- Estado de procesamiento en tiempo real
- Integración con Elasticsearch

