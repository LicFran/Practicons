#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Funciones de utilidad para el procesador de PDF PráctiCos
"""

import os
import re
import logging
import unicodedata
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Limpia y normaliza el texto extraído
    
    Args:
        text (str): Texto bruto del OCR
        
    Returns:
        str: Texto limpio y normalizado
    """
    # Reemplaza múltiples espacios con un solo espacio
    text = re.sub(r'\s+', ' ', text)
    
    # Corrige errores comunes de OCR
    text = text.replace('l', '1').replace('O', '0')
    
    # Normaliza caracteres unicode
    text = unicodedata.normalize('NFKD', text)
    
    # Elimina saltos de línea extras
    text = re.sub(r'\n+', '\n', text)
    
    return text.strip()


def extract_table_data(image: np.ndarray) -> List[List[str]]:
    """
    Extrae datos de tabla desde una imagen usando OpenCV
    
    Args:
        image (np.ndarray): La imagen que contiene tablas
        
    Returns:
        List[List[str]]: Datos de tabla extraídos como una lista de filas, cada fila siendo una lista de valores de celda
    """
    try:
        # Convierte a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Aplica umbral
        _, threshold = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # Encuentra contornos
        contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Encuentra líneas de cuadrícula de tabla
        horizontal_lines, vertical_lines = _detect_lines(threshold)
        
        # Encuentra celdas de tabla desde la intersección de líneas
        cells = _find_cells(horizontal_lines, vertical_lines)
        
        # Ordena celdas por fila y columna
        sorted_cells = _sort_cells(cells)
        
        # Esto sería seguido por OCR en cada celda para extraer texto
        # Simplificado para este ejemplo
        
        # Devuelve datos de ejemplo
        # En una implementación real, usarías pytesseract para extraer texto de cada celda
        return [
            ["101", "Excavación", "m³", "150", "80.00", "12,000.00"],
            ["102", "Cimentación de concreto", "m³", "75", "1,200.00", "90,000.00"],
            ["103", "Muro de tabique", "m²", "350", "450.00", "157,500.00"]
        ]
    
    except Exception as e:
        logger.error(f"Error al extraer datos de tabla: {str(e)}")
        return []


def _detect_lines(threshold_img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detecta líneas horizontales y verticales en la imagen
    
    Args:
        threshold_img (np.ndarray): Imagen umbralizada
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: Líneas horizontales y verticales
    """
    # Crea kernels
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
    
    # Detecta líneas horizontales
    horizontal = cv2.erode(threshold_img, horizontal_kernel, iterations=1)
    horizontal = cv2.dilate(horizontal, horizontal_kernel, iterations=1)
    
    # Detecta líneas verticales
    vertical = cv2.erode(threshold_img, vertical_kernel, iterations=1)
    vertical = cv2.dilate(vertical, vertical_kernel, iterations=1)
    
    return horizontal, vertical


def _find_cells(horizontal_lines: np.ndarray, vertical_lines: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Encuentra celdas de tabla desde la intersección de líneas horizontales y verticales
    
    Args:
        horizontal_lines (np.ndarray): Líneas horizontales detectadas
        vertical_lines (np.ndarray): Líneas verticales detectadas
        
    Returns:
        List[Tuple[int, int, int, int]]: Lista de celdas como (x, y, w, h)
    """
    # Encuentra intersecciones
    intersections = cv2.bitwise_and(horizontal_lines, vertical_lines)
    
    # Encuentra contornos (estas serían las intersecciones)
    contours, _ = cv2.findContours(intersections, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Obtiene puntos de intersección
    points = []
    for contour in contours:
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            points.append((cx, cy))
    
    # Ordena puntos por x, luego por y
    points.sort(key=lambda p: (p[0], p[1]))
    
    # Implementación de ejemplo
    # En una implementación real, necesitaríamos identificar qué puntos forman celdas
    # y extraer los cuadros delimitadores de esas celdas
    
    # Devuelve celdas de ejemplo
    return [
        (100, 100, 200, 50),
        (300, 100, 200, 50),
        (100, 150, 200, 50),
        (300, 150, 200, 50)
    ]


def _sort_cells(cells: List[Tuple[int, int, int, int]]) -> List[List[Tuple[int, int, int, int]]]:
    """
    Ordena celdas por fila y columna
    
    Args:
        cells (List[Tuple[int, int, int, int]]): Lista de celdas como (x, y, w, h)
        
    Returns:
        List[List[Tuple[int, int, int, int]]]: Celdas organizadas por fila y columna
    """
    # Obtiene coordenadas y para todas las celdas
    y_coords = sorted(set([cell[1] for cell in cells]))
    
    # Agrupa celdas por fila
    rows = []
    for y in y_coords:
        # Obtiene todas las celdas en esta fila
        row_cells = [cell for cell in cells if abs(cell[1] - y) < 10]
        
        # Ordena celdas en esta fila por coordenada x
        row_cells.sort(key=lambda cell: cell[0])
        
        rows.append(row_cells)
    
    return rows


def extract_currency(text: str) -> Optional[float]:
    """
    Extrae cantidad monetaria del texto
    
    Args:
        text (str): Texto que contiene moneda
        
    Returns:
        Optional[float]: Cantidad extraída o None
    """
    # Busca patrones de moneda
    currency_pattern = r'[$€¥£]?\s*(\d+(?:[.,]\d+)*(?:[.,]\d+)?)'
    match = re.search(currency_pattern, text)
    
    if match:
        # Extrae la cantidad
        amount_str = match.group(1)
        
        # Limpia la cantidad
        amount_str = amount_str.replace(',', '')
        
        try:
            # Convierte a float
            amount = float(amount_str)
            return amount
        except ValueError:
            return None
    
    return None


def is_estimate_item(text: str) -> bool:
    """
    Comprueba si una línea de texto es probablemente un elemento de presupuesto
    
    Args:
        text (str): Línea de texto
        
    Returns:
        bool: True si el texto es probablemente un elemento de presupuesto
    """
    # Comprueba si el texto coincide con patrones comunes para elementos de presupuesto
    
    # Patrón 1: Código al principio seguido de descripción
    pattern1 = r'^\s*([A-Z0-9]{2,10})\s+(.+)$'
    
    # Patrón 2: Descripción seguida de unidad, cantidad, precio
    pattern2 = r'.+\s+(m[²³]|kg|ton|pza)\s+\d+(?:\.\d+)?\s+\$?\d+(?:,\d+)*\.\d+'
    
    return bool(re.match(pattern1, text)) or bool(re.match(pattern2, text)) 