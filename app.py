"""
app.py
Punto de entrada en la raíz del proyecto.
Permite iniciar el servidor directamente con:
    python app.py
tanto desde la raíz (C:\\xampp\\htdocs\\codigo) como desde cualquier ubicación.
"""
import os
import sys
import runpy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Cambiar el directorio de trabajo a backend para que las rutas relativas funcionen
os.chdir(BACKEND_DIR)

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

if __name__ == "__main__":
    app_path = os.path.join(BACKEND_DIR, "app.py")
    runpy.run_path(app_path, run_name="__main__")

