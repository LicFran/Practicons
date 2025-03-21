#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo exportador de Excel para guardar datos extraídos de presupuestos de construcción
"""

import os
import logging
from pathlib import Path
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from src.config import DEFAULT_SHEET_NAME, TABLE_HEADERS

logger = logging.getLogger(__name__)


class ExcelExporter:
    """
    Clase para exportar datos extraídos de presupuestos de construcción a Excel
    """
    
    def __init__(self, data, output_path):
        """
        Inicializa el exportador de Excel
        
        Args:
            data (dict): Datos extraídos del PDF con metadatos, tablas, etc.
            output_path (str or Path): Ruta al archivo Excel de salida
        """
        self.data = data
        self.output_path = Path(output_path)
        self.workbook = None
        
        # Definir estilos para el Excel
        self.header_font = Font(bold=True, size=12, color="FFFFFF")
        self.header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        self.header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Bordes para las celdas
        self.border = Border(
            left=Side(style='thin'), 
            right=Side(style='thin'), 
            top=Side(style='thin'), 
            bottom=Side(style='thin')
        )
    
    def export(self):
        """
        Exporta los datos extraídos a un archivo Excel formateado
        
        Returns:
            Path: Ruta al archivo Excel generado
        """
        logger.info(f"Exportando datos a Excel: {self.output_path}")
        
        # Crear un nuevo libro de trabajo
        self.workbook = openpyxl.Workbook()
        
        # Eliminar la hoja predeterminada
        default_sheet = self.workbook.active
        self.workbook.remove(default_sheet)
        
        # Crear hojas para diferentes tipos de datos
        self._create_main_sheet()         # Hoja principal para tablas
        self._create_metadata_sheet()     # Hoja para metadatos
        self._create_sections_sheet()     # Hoja para secciones de texto
        
        # Guardar el archivo Excel
        self.workbook.save(self.output_path)
        logger.info(f"Archivo Excel guardado con éxito: {self.output_path}")
        
        return self.output_path
    
    def _create_main_sheet(self):
        """Crear hoja principal con datos de tablas"""
        # Obtener datos de tablas
        tables = self.data.get("tables", [])
        if not tables:
            # Crear una hoja principal vacía si no hay tablas
            sheet = self.workbook.create_sheet(DEFAULT_SHEET_NAME)
            sheet["A1"] = "No se encontraron tablas en el documento"
            return
        
        # Crear la hoja principal
        sheet = self.workbook.create_sheet(DEFAULT_SHEET_NAME)
        
        # Combinar todos los datos de tablas
        all_data = []
        for table in tables:
            all_data.extend(table.get("data", []))
        
        if not all_data:
            sheet["A1"] = "No se encontraron datos en las tablas"
            return
        
        # Escribir encabezados
        for col_idx, header in enumerate(TABLE_HEADERS, start=1):
            cell = sheet.cell(row=1, column=col_idx, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.border
            # Ajustar ancho de columna basado en la longitud de los encabezados
            sheet.column_dimensions[get_column_letter(col_idx)].width = max(len(header) + 2, 15)
        
        # Escribir datos de tabla
        for row_idx, item in enumerate(all_data, start=2):
            # Asegurarse de que los datos tienen el formato correcto
            if isinstance(item, dict):
                # Para cada columna de encabezado, buscar los valores correspondientes
                for col_idx, header in enumerate(TABLE_HEADERS, start=1):
                    # Manejar diferentes formatos de nombres de claves
                    key = header.lower().replace(" ", "_")
                    alt_key = header.lower()
                    
                    # Buscar el valor usando diferentes formatos de claves
                    value = item.get(key, item.get(alt_key, ""))
                    
                    # Escribir el valor en la celda
                    cell = sheet.cell(row=row_idx, column=col_idx, value=value)
                    cell.border = self.border
                    
                    # Alinear cantidades numéricas a la derecha
                    if col_idx in [4, 5, 6]:  # Columnas numéricas
                        try:
                            if isinstance(value, str):
                                # Limpiar y convertir a número si es posible
                                clean_value = value.replace(",", "").replace("$", "").strip()
                                if clean_value:
                                    cell.value = float(clean_value)
                                    cell.number_format = "#,##0.00"
                            cell.alignment = Alignment(horizontal="right")
                        except ValueError:
                            # Si no se puede convertir a número, dejarlo como está
                            pass
            elif isinstance(item, list):
                # Manejar lista de valores
                for col_idx, value in enumerate(item, start=1):
                    if col_idx <= len(TABLE_HEADERS):
                        cell = sheet.cell(row=row_idx, column=col_idx, value=value)
                        cell.border = self.border
        
        # Ajustar el ancho de las columnas basado en el contenido
        for col_idx in range(1, len(TABLE_HEADERS) + 1):
            max_length = 0
            column = get_column_letter(col_idx)
            for row_idx in range(1, len(all_data) + 2):
                cell_value = sheet.cell(row=row_idx, column=col_idx).value
                if cell_value:
                    max_length = max(max_length, len(str(cell_value)))
            adjusted_width = max(max_length + 2, 15)
            sheet.column_dimensions[column].width = min(adjusted_width, 50)  # Limitar el ancho máximo
        
        # Aplicar autofilter en los encabezados
        sheet.auto_filter.ref = f"A1:{get_column_letter(len(TABLE_HEADERS))}{len(all_data) + 1}"
        
        # Congelar la fila de encabezados
        sheet.freeze_panes = "A2"
    
    def _create_metadata_sheet(self):
        """Crear hoja de metadatos"""
        # Obtener metadatos
        metadata = self.data.get("metadata", {})
        enhanced_metadata = self.data.get("enhanced_metadata", {})
        
        # Combinar metadatos regulares y mejorados por IA
        combined_metadata = {**metadata}
        if enhanced_metadata:
            combined_metadata.update({k: v for k, v in enhanced_metadata.items() if v and not combined_metadata.get(k)})
        
        if not combined_metadata:
            return  # No crear la hoja si no hay metadatos
        
        # Crear hoja de metadatos
        sheet = self.workbook.create_sheet("Metadatos")
        
        # Encabezados
        sheet["A1"] = "Campo"
        sheet["B1"] = "Valor"
        
        # Aplicar formato a los encabezados
        for cell in [sheet["A1"], sheet["B1"]]:
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.border
        
        # Establecer ancho de columnas
        sheet.column_dimensions["A"].width = 25
        sheet.column_dimensions["B"].width = 50
        
        # Escribir metadatos
        row_idx = 2
        for key, value in combined_metadata.items():
            if value:  # Solo incluir valores no vacíos
                # Formatear la clave para mejor legibilidad
                display_key = key.replace("_", " ").title()
                
                sheet.cell(row=row_idx, column=1, value=display_key).border = self.border
                cell = sheet.cell(row=row_idx, column=2, value=value)
                cell.border = self.border
                cell.alignment = Alignment(wrap_text=True)
                row_idx += 1
        
        # Aplicar autofilter
        sheet.auto_filter.ref = f"A1:B{row_idx - 1}"
        
        # Congelar la fila de encabezados
        sheet.freeze_panes = "A2"
    
    def _create_sections_sheet(self):
        """Crear hoja de secciones"""
        # Obtener secciones
        sections = self.data.get("sections", {})
        
        if not sections:
            return  # No crear la hoja si no hay secciones
        
        # Crear hoja de secciones
        sheet = self.workbook.create_sheet("Secciones")
        
        # Encabezados
        sheet["A1"] = "Sección"
        sheet["B1"] = "Contenido"
        
        # Aplicar formato a los encabezados
        for cell in [sheet["A1"], sheet["B1"]]:
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.border
        
        # Establecer ancho de columnas
        sheet.column_dimensions["A"].width = 25
        sheet.column_dimensions["B"].width = 75
        
        # Escribir secciones
        row_idx = 2
        for section_name, content in sections.items():
            sheet.cell(row=row_idx, column=1, value=section_name).border = self.border
            cell = sheet.cell(row=row_idx, column=2, value=content)
            cell.border = self.border
            cell.alignment = Alignment(wrap_text=True)
            row_idx += 1
        
        # Congelar la fila de encabezados
        sheet.freeze_panes = "A2"
        
    # Nota: La función _create_summary_sheet ha sido eliminada porque
    # ya no generamos resúmenes. El enfoque es únicamente extraer y 
    # organizar datos sin realizar análisis. 