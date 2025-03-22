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
        self._create_proyecto_sheet()     # Hoja para datos del proyecto
        self._create_materiales_sheet()   # Hoja para listado de materiales
        
        # Guardar el archivo Excel
        self.workbook.save(self.output_path)
        logger.info(f"Archivo Excel guardado con éxito: {self.output_path}")
        
        return self.output_path
    
    def _create_proyecto_sheet(self):
        """Crear hoja para datos del proyecto"""
        # Obtener metadatos y datos del proyecto
        metadata = self.data.get("metadata", {})
        datos_proyecto = self.data.get("datos_proyecto", {})
        
        # Combinar datos regulares y mejorados por IA
        combined_data = {**metadata}
        if datos_proyecto:
            combined_data.update({k: v for k, v in datos_proyecto.items() if v and not combined_data.get(k)})
        
        if not combined_data:
            # Crear una hoja vacía si no hay datos
            sheet = self.workbook.create_sheet("Proyecto")
            sheet["A1"] = "No se encontraron datos del proyecto"
            return
        
        # Crear hoja de proyecto
        sheet = self.workbook.create_sheet("Proyecto")
        
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
        
        # Escribir datos del proyecto
        row_idx = 2
        for key, value in combined_data.items():
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
    
    def _create_materiales_sheet(self):
        """Crear hoja para listado y precios de materiales"""
        # Obtener lista de materiales
        materiales = self.data.get("materiales", [])
        
        if not materiales:
            # Intentar obtener datos de tablas si no hay materiales específicos
            tables = self.data.get("tables", [])
            all_data = []
            for table in tables:
                all_data.extend(table.get("data", []))
            
            if not all_data:
                # Crear una hoja vacía si no hay datos
                sheet = self.workbook.create_sheet("Materiales")
                sheet["A1"] = "No se encontraron datos de materiales"
                return
            
            # Usar datos de tablas como materiales
            materiales = all_data
        
        # Crear hoja de materiales
        sheet = self.workbook.create_sheet("Materiales")
        
        # Definir encabezados para la hoja de materiales
        headers = ["Material", "Unidades", "Precio Unitario", "Precio Total"]
        
        # Escribir encabezados
        for col_idx, header in enumerate(headers, start=1):
            cell = sheet.cell(row=1, column=col_idx, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.border
            # Ajustar ancho de columna
            sheet.column_dimensions[get_column_letter(col_idx)].width = max(len(header) + 2, 15)
        
        # Escribir datos de materiales
        for row_idx, item in enumerate(materiales, start=2):
            if isinstance(item, dict):
                # Asignar valores a las columnas correspondientes
                values = [
                    item.get("material", item.get("nombre", "")),
                    item.get("units", item.get("unidades", "")),
                    item.get("unit_price", item.get("precio_unitario", "")),
                    item.get("total_price", item.get("precio_total", ""))
                ]
                
                for col_idx, value in enumerate(values, start=1):
                    cell = sheet.cell(row=row_idx, column=col_idx, value=value)
                    cell.border = self.border
                    
                    # Formatear valores numéricos
                    if col_idx in [3, 4]:  # Columnas de precios
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
                # Si es una lista, interpretar las primeras columnas como materiales
                for col_idx, value in enumerate(item[:4], start=1):  # Limitar a las primeras 4 columnas
                    cell = sheet.cell(row=row_idx, column=col_idx, value=value)
                    cell.border = self.border
                    if col_idx in [3, 4]:
                        cell.alignment = Alignment(horizontal="right")
        
        # Ajustar el ancho de las columnas
        for col_idx in range(1, len(headers) + 1):
            max_length = 0
            column = get_column_letter(col_idx)
            for row_idx in range(1, len(materiales) + 2):
                cell_value = sheet.cell(row=row_idx, column=col_idx).value
                if cell_value:
                    max_length = max(max_length, len(str(cell_value)))
            adjusted_width = max(max_length + 2, 15)
            sheet.column_dimensions[column].width = min(adjusted_width, 50)  # Limitar el ancho máximo
        
        # Aplicar autofilter y congelar encabezados
        sheet.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(materiales) + 1}"
        sheet.freeze_panes = "A2"
    