#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de configuración para PractiCons
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Directorios base
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = os.path.join(BASE_DIR, "data", "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")

# Configuración de OCR
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "tesseract")
OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "spa")
OCR_DPI = int(os.getenv("OCR_DPI", "300"))

# Configuración de IA
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_AI_EXTRACTION = False  # Desactivado explícitamente

# Configuración de procesamiento de PDF
IMAGE_FORMAT = "PNG"
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Configuración de exportación a Excel
DEFAULT_SHEET_NAME = "Presupuesto"
TABLE_HEADERS = [
    "Cliente", 
    "Celular", 
    "Tel-Fijo", 
    "Dirección", 
    "E-mail", 
    "Orden de Trabajo",
    "M2",
    "Mano de Obra",
    "Material",
    "Total Material",
    "Total Mano de Obra",
    "Total General"
]

# Secciones de presupuesto para extracción
ESTIMATE_SECTIONS = [
    "Presupuesto",
    "Materiales",
    "Mano de Obra",
    "Detalle de Materiales",
    "Observaciones",
    "Condiciones de Pago",
    "Totales"
]
