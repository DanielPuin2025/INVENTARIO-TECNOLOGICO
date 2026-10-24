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

# Copiar requirements del backend
COPY backend/requirements.txt ./backend/requirements.txt

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copiar código de la aplicación
COPY backend/ ./backend/

# Crear directorios necesarios
RUN mkdir -p backend/uploads backend/imagenes

# Exponer puerto
EXPOSE 5000

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1

# Cambiar al directorio backend y ejecutar
WORKDIR /app/backend
CMD ["python", "app.py"]
