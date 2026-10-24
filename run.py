"""Compatibilidad con el comando histórico ``python run.py``."""
import os
import runpy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    runpy.run_path(os.path.join(BASE_DIR, "app.py"), run_name="__main__")
