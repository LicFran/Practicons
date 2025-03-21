#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo principal para PráctiCos - Digitalizador de Presupuestos de Construcción en PDF
"""

import os
import sys
import logging
from pathlib import Path

# Añadir directorio padre a la ruta para habilitar importaciones
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pdf_processor import PDFProcessor
from src.excel_exporter import ExcelExporter
from src.config import INPUT_DIR, OUTPUT_DIR


def setup_logging():
    """Configurar el registro (logging) para la aplicación"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('practicos.log')
        ]
    )
    return logging.getLogger(__name__)


def main():
    """Punto de entrada principal para la aplicación"""
    logger = setup_logging()
    logger.info("Iniciando el procesamiento PDF de PráctiCos")
    
    # Crear directorio de salida si no existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Listar archivos PDF en el directorio de entrada
    pdf_files = list(Path(INPUT_DIR).glob('*.pdf'))
    
    if not pdf_files:
        logger.warning(f"No se encontraron archivos PDF en {INPUT_DIR}")
        return
    
    logger.info(f"Se encontraron {len(pdf_files)} archivos PDF para procesar")
    
    # Procesar cada archivo PDF
    for pdf_path in pdf_files:
        try:
            logger.info(f"Procesando {pdf_path}")
            
            # Inicializar el procesador de PDF
            processor = PDFProcessor(pdf_path)
            
            # Extraer datos del PDF
            extracted_data = processor.extract_data()
            
            # Exportar datos a Excel
            output_file = Path(OUTPUT_DIR) / f"{pdf_path.stem}.xlsx"
            exporter = ExcelExporter(extracted_data, output_file)
            exporter.export()
            
            logger.info(f"Se procesó con éxito {pdf_path} y se guardó en {output_file}")
            
        except Exception as e:
            logger.error(f"Error al procesar {pdf_path}: {str(e)}")


if __name__ == "__main__":
    main() 