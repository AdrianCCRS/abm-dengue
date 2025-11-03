# Dockerfile para ABM-Dengue-Bucaramanga
# Uso: docker build -t abm-dengue .
#      docker run -v $(pwd)/results:/app/results abm-dengue

FROM python:3.10-slim

# Metadatos
LABEL maintainer="UIS - Simulación Digital F1"
LABEL description="Simulación ABM para dengue en Bucaramanga"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/

# Crear directorios para resultados
RUN mkdir -p /app/results/plots

# Comando por defecto
CMD ["python", "src/main.py"]
