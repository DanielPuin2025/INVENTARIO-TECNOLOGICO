# Dockerfile para Sistema de Inventario Tecnológico
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para MySQL
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p backend/uploads backend/imagenes backend/static backend/templates

# Exponer puerto
EXPOSE 5000

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1

# Comando para iniciar la aplicación
CMD ["python", "app.py"]
