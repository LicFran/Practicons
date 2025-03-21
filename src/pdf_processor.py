#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de procesamiento de PDF para extraer datos de presupuestos de construcción
"""

import os
import logging
import tempfile
import json
from pathlib import Path
import numpy as np
import cv2
import PyPDF2
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

from src.config import TESSERACT_PATH, OCR_LANGUAGE, OCR_DPI, TEMP_DIR, IMAGE_FORMAT
from src.utils import clean_text, extract_table_data
from src.ai_extractor import AIExtractor

# Configurar pytesseract
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Asegurar que el directorio temporal existe
os.makedirs(TEMP_DIR, exist_ok=True)

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Clase para procesar presupuestos de construcción en PDF y extraer datos relevantes
    """
    
    def __init__(self, pdf_path):
        """
        Inicializa el procesador de PDF
        
        Args:
            pdf_path (str or Path): Ruta al archivo PDF
        """
        self.pdf_path = Path(pdf_path)
        self.pages = []
        self.text_content = ""
        self.extracted_data = {
            "metadata": {},
            "sections": {},
            "tables": [],
            "summary": {}
        }
        self.ai_extractor = AIExtractor()
        
    def extract_data(self):
        """
        Extrae todos los datos del PDF
        
        Returns:
            dict: Datos extraídos con metadatos, secciones, tablas y resumen
        """
        # Convertir PDF a imágenes
        self._convert_pdf_to_images()
        
        # Extraer texto usando OCR
        self._extract_text_from_images()
        
        # Procesar texto extraído
        self._process_text()
        
        # Extraer tablas de las imágenes
        self._extract_tables()
        
        # Aplicar extracción basada en IA para obtener información adicional
        self._apply_ai_extraction()
        
        return self.extracted_data
        
    def _convert_pdf_to_images(self):
        """Convertir páginas de PDF a imágenes para procesamiento"""
        logger.info(f"Convirtiendo PDF a imágenes: {self.pdf_path}")
        
        try:
            # Convertir PDF a imágenes
            self.pages = convert_from_path(
                self.pdf_path,
                dpi=OCR_DPI,
                output_folder=TEMP_DIR,
                fmt=IMAGE_FORMAT.lower(),
                thread_count=4,
                use_pdftocairo=True,
                grayscale=False
            )
            
            logger.info(f"Convertidas {len(self.pages)} páginas a imágenes")
        except Exception as e:
            logger.error(f"Error al convertir PDF a imágenes: {str(e)}")
            raise
    
    def _extract_text_from_images(self):
        """Extraer texto de las imágenes de página PDF usando OCR"""
        logger.info("Extrayendo texto de las imágenes PDF")
        full_text = []
        
        for i, page in enumerate(self.pages):
            try:
                # Aplicar OCR para extraer texto
                config = f'--oem 3 --psm 6 -l {OCR_LANGUAGE}'
                text = pytesseract.image_to_string(page, config=config)
                
                # Limpiar y normalizar el texto
                text = clean_text(text)
                
                # Añadir referencia de número de página
                page_text = f"---PÁGINA {i+1}---\n{text}\n"
                full_text.append(page_text)
                
            except Exception as e:
                logger.error(f"Error al extraer texto de la página {i+1}: {str(e)}")
        
        self.text_content = "\n".join(full_text)
        logger.info(f"Extraídas {len(full_text)} páginas de texto")
    
    def _process_text(self):
        """Procesar el texto extraído para identificar secciones y metadatos"""
        logger.info("Procesando texto extraído")
        
        # Extraer metadatos básicos (fecha del documento, nombre del proyecto, cliente)
        self._extract_metadata()
        
        # Identificar y extraer secciones del presupuesto de construcción
        self._extract_sections()
    
    def _extract_metadata(self):
        """Extraer metadatos del contenido de texto"""
        # Extraer nombre del proyecto, cliente, fecha, etc.
        # Esta implementación dependería del formato específico de los documentos
        # Por ahora, usando lógica de extracción provisional
        
        lines = self.text_content.split('\n')
        metadata = {
            "project_name": "",
            "client": "",
            "date": "",
            "location": "",
            "total_amount": ""
        }
        
        # Extracción simple basada en palabras clave
        for line in lines:
            line = line.strip()
            if "proyecto" in line.lower() and not metadata["project_name"]:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    metadata["project_name"] = parts[1].strip()
            
            elif "cliente" in line.lower() and not metadata["client"]:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    metadata["client"] = parts[1].strip()
            
            elif "fecha" in line.lower() and not metadata["date"]:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    metadata["date"] = parts[1].strip()
            
            elif "ubicación" in line.lower() and not metadata["location"]:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    metadata["location"] = parts[1].strip()
            
            elif "total" in line.lower() and not metadata["total_amount"]:
                # Buscar cantidades monetarias
                if "$" in line:
                    parts = line.split("$", 1)
                    if len(parts) > 1:
                        amount = parts[1].strip().replace(",", "")
                        metadata["total_amount"] = amount
        
        self.extracted_data["metadata"] = metadata
        logger.info(f"Metadatos extraídos: {metadata}")
    
    def _extract_sections(self):
        """Extraer diferentes secciones del presupuesto de construcción"""
        # Esto dependería del formato específico de los documentos
        # Implementando una extracción de sección simple basada en encabezados comunes
        
        from src.config import ESTIMATE_SECTIONS
        
        text = self.text_content
        sections = {}
        
        for section_name in ESTIMATE_SECTIONS:
            if section_name.lower() in text.lower():
                # Encontrar la sección en el texto
                start_idx = text.lower().find(section_name.lower())
                
                # Encontrar la siguiente sección (si existe)
                next_section_idx = float('inf')
                for next_section in ESTIMATE_SECTIONS:
                    if next_section != section_name:
                        idx = text.lower().find(next_section.lower(), start_idx + len(section_name))
                        if idx != -1 and idx < next_section_idx:
                            next_section_idx = idx
                
                if next_section_idx == float('inf'):
                    # Si no hay siguiente sección, extraer hasta el final
                    section_text = text[start_idx:].strip()
                else:
                    section_text = text[start_idx:next_section_idx].strip()
                
                sections[section_name] = section_text
        
        self.extracted_data["sections"] = sections
        logger.info(f"Extraídas {len(sections)} secciones")
    
    def _extract_tables(self):
        """Extraer tablas de las imágenes PDF"""
        logger.info("Extrayendo tablas de las imágenes PDF")
        tables = []
        
        for i, page in enumerate(self.pages):
            try:
                # Convertir imagen PIL a formato OpenCV
                img = np.array(page)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                # Procesar imagen para detectar tablas
                table_data = extract_table_data(img)
                
                if table_data:
                    tables.append({
                        "page": i + 1,
                        "data": table_data
                    })
                
            except Exception as e:
                logger.error(f"Error al extraer tablas de la página {i+1}: {str(e)}")
        
        self.extracted_data["tables"] = tables
        logger.info(f"Extraídas {len(tables)} tablas")
    
    def _apply_ai_extraction(self):
        """Aplicar extracción basada en IA para obtener información adicional"""
        try:
            # Usar la clase AIExtractor para extraer información adicional
            enhanced_data = self.ai_extractor.enhance_extraction(
                self.text_content, 
                self.extracted_data
            )
            
            # Actualizar los datos extraídos con información mejorada por IA
            self.extracted_data.update(enhanced_data)
            
            # Ya no generamos un resumen del presupuesto
            # El método generate_summary ahora devuelve un diccionario vacío
            self.extracted_data["summary"] = {}
            
            logger.info("Aplicada extracción por IA con éxito")
        except Exception as e:
            logger.error(f"Error en la extracción por IA: {str(e)}")
            # Continuar sin extracción por IA si falla 