#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de extracción basado en IA para mejorar la extracción de datos de presupuestos de construcción
"""

import os
import logging
import json
from pathlib import Path
import re
from typing import Dict, List, Any, Optional

from src.config import OPENAI_API_KEY, USE_AI_EXTRACTION

logger = logging.getLogger(__name__)


class AIExtractor:
    """
    Clase para utilizar IA en la extracción de datos de presupuestos de construcción
    """
    
    def __init__(self):
        """Inicializa el extractor de IA"""
        self.api_key = OPENAI_API_KEY
        self.use_ai = USE_AI_EXTRACTION
        
        # Si la extracción por IA está habilitada pero no se proporciona una clave API, registrar una advertencia
        if self.use_ai and not self.api_key:
            logger.warning("La extracción por IA está habilitada pero no se proporcionó una clave API de OpenAI")
            self.use_ai = False
    
    def enhance_extraction(self, text_content: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Utiliza IA para extraer datos estructurados
        
        Args:
            text_content (str): El contenido de texto sin procesar del PDF
            extracted_data (dict): Datos previamente extraídos
            
        Returns:
            dict: Datos estructurados extraídos por IA
        """
        if not self.use_ai:
            logger.info("La extracción por IA está deshabilitada, omitiendo extracción")
            return {}
        
        try:
            logger.info("Extrayendo datos con IA")
            
            # Usar langchain si está disponible, de lo contrario recurrir a llamadas directas a la API
            try:
                from langchain.llms import OpenAI
                from langchain.chains import LLMChain
                from langchain.prompts import PromptTemplate
                
                return self._enhance_with_langchain(text_content, extracted_data)
            except ImportError:
                logger.info("LangChain no está disponible, recurriendo a llamadas directas a la API")
                return self._enhance_with_direct_api(text_content, extracted_data)
                
        except Exception as e:
            logger.error(f"Error al extraer datos con IA: {str(e)}")
            return {}
    
    def _enhance_with_langchain(self, text_content: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Utiliza LangChain para mejorar la extracción
        
        Args:
            text_content (str): El contenido de texto sin procesar del PDF
            extracted_data (dict): Datos previamente extraídos
            
        Returns:
            dict: Datos mejorados
        """
        from langchain.llms import OpenAI
        from langchain.chains import LLMChain
        from langchain.prompts import PromptTemplate
        
        # Crear un prompt para extraer datos del presupuesto
        prompt_template = """
        Eres un experto en presupuestos. 
        Estás analizando un documento de presupuesto de construcción. 
        
        El documento contiene el siguiente texto:
        {text_content}
        
        Basándote en el texto anterior, extrae ÚNICAMENTE la siguiente información en formato JSON:
        
        1. Metadatos del proyecto: cliente, celular, telefono_fijo, direccion, fecha, e-mail, orden_trabajo
        2. Detalle de materiales y precios: material, unidades, precio_unitario, precio_total, cantidad_m2, mano_obra, total_material, total_mano_obra, total_general
        
        Devuelve el resultado como un objeto JSON con la siguiente estructura:
        {{
            "enhanced_metadata": {{
                "client": "string",
                "phone": "string",
                "phone_fixed": "string",
                "address": "string",
                "email": "string",
                "date": "string", 
                "work_order": "string",
                "quantity_m2": "number",
                "mano_obra": "number",
                "total_material": "number",
                "total_general": "number"
            }},
            "key_items": [
                {{
                    "material": "string",
                    "units": "string",
                    "unit_price": "number",
                    "total_price": "number",
                }}
            ]
        }}
        """
        
        # Crear una versión truncada del texto si es demasiado largo
        max_content_length = 4000  # Ajustar según la ventana de contexto del modelo
        truncated_text = text_content[:max_content_length] if len(text_content) > max_content_length else text_content
        
        # Crear el prompt
        prompt = PromptTemplate(
            input_variables=["text_content"],
            template=prompt_template
        )
        
        # Inicializar el LLM
        llm = OpenAI(
            openai_api_key=self.api_key,
            temperature=0.2,
            max_tokens=1000
        )
        
        # Crear la cadena
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # Ejecutar la cadena
        result = chain.run(text_content=truncated_text)
        
        # Procesar el resultado
        try:
            # Extraer los datos JSON (manejar caso donde puede haber bloques de código markdown)
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                json_str = result.split("```")[1].strip()
            else:
                json_str = result.strip()
            
            # Analizar los datos JSON
            enhanced_data = json.loads(json_str)
            return enhanced_data
        
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Error al analizar la respuesta de la IA: {str(e)}")
            return {}
    
    def _enhance_with_direct_api(self, text_content: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Utiliza llamadas directas a la API de OpenAI para mejorar la extracción
        
        Args:
            text_content (str): El contenido de texto sin procesar del PDF
            extracted_data (dict): Datos previamente extraídos
            
        Returns:
            dict: Datos mejorados
        """
        try:
            import openai
            
            # Configure the API key
            openai.api_key = self.api_key
            
            # Create a truncated version of the text if it's too long
            max_content_length = 4000  # Adjust based on the model's context window
            truncated_text = text_content[:max_content_length] if len(text_content) > max_content_length else text_content
            
            # Create the prompt
            prompt = f"""
            Eres un experto en presupuestos. 
            Estás analizando un documento de presupuesto de construcción. 
            
            El documento contiene el siguiente texto:
            {truncated_text}
            
            Basándote en el texto anterior, extrae ÚNICAMENTE la siguiente información en formato JSON:
            
            1. Metadatos del proyecto: cliente, celular, telefono_fijo, direccion, fecha, e-mail, orden_trabajo
            2. Detalle de materiales y precios: material, unidades, precio_unitario, precio_total, cantidad_m2, mano_obra, total_material, total_mano_obra, total_general
            
            Devuelve el resultado como un objeto JSON con la siguiente estructura:
            {{
                "enhanced_metadata": {{
                    "client": "string",
                    "phone": "string",
                    "phone_fixed": "string",
                    "address": "string",
                    "email": "string",
                    "date": "string", 
                    "work_order": "string",
                    "quantity_m2": "number",
                    "mano_obra": "number",
                    "total_material": "number",
                    "total_general": "number"
                }},
                "key_items": [
                    {{
                        "material": "string",
                        "units": "string",
                        "unit_price": "number",
                        "total_price": "number",
                    }}
                ]
            }}
            """
            
            # Call the OpenAI API with updated client
            client = openai.OpenAI(api_key=self.api_key)
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=1000,
                temperature=0.2
            )
            
            # Extract the response text
            result = response.choices[0].text.strip()
            
            # Process the result
            try:
                # Extract the JSON data (handle case where there might be markdown code blocks)
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()
                else:
                    json_str = result.strip()
                
                # Parse the JSON data
                enhanced_data = json.loads(json_str)
                return enhanced_data
            
            except (json.JSONDecodeError, IndexError) as e:
                logger.error(f"Error parsing AI response: {str(e)}")
                return {}
        
        except Exception as e:
            logger.error(f"Error making direct API call: {str(e)}")
            return {}
    
    def generate_summary(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Función deshabilitada - ya no genera resúmenes
        
        Args:
            extracted_data (dict): Los datos extraídos
            
        Returns:
            dict: Diccionario vacío
        """
        logger.info("La generación de resúmenes está deshabilitada")
        return {} 