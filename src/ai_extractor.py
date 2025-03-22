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
        Extrae la siguiente información del texto del documento:
        
        El documento contiene el siguiente texto:
        {text_content}
        
        Extrae ÚNICAMENTE los siguientes datos en formato JSON:
        
        1. Datos del proyecto: nombre_proyecto, cliente, celular, telefono_fijo, direccion, email, fecha, orden_trabajo, total_materiales, total_mano_obra, total_proyecto
        2. Lista de materiales: material, unidades, precio_unitario, precio_total
        
        Devuelve el resultado como un objeto JSON con la siguiente estructura:
        {{
            "datos_proyecto": {{
                "nombre_proyecto": "string",
                "cliente": "string",
                "celular": "string",
                "telefono_fijo": "string",
                "direccion": "string",
                "email": "string",
                "fecha": "string", 
                "orden_trabajo": "string",
                "total_materiales": "number",
                "total_mano_obra": "number",
                "total_proyecto": "number"
            }},
            "materiales": [
                {{
                    "material": "string",
                    "unidades": "string",
                    "precio_unitario": "number",
                    "precio_total": "number"
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
            
            # Configurar la clave API
            openai.api_key = self.api_key
            
            # Crear una versión truncada del texto si es demasiado largo
            max_content_length = 4000  # Ajustar según la ventana de contexto del modelo
            truncated_text = text_content[:max_content_length] if len(text_content) > max_content_length else text_content
            
            # Crear el prompt
            prompt = f"""
            Extrae la siguiente información del texto del documento:
            
            El documento contiene el siguiente texto:
            {truncated_text}
            
            Extrae ÚNICAMENTE los siguientes datos en formato JSON:
            
            1. Datos del proyecto: nombre_proyecto, cliente, celular, telefono_fijo, direccion, email, fecha, orden_trabajo, total_materiales, total_mano_obra, total_proyecto
            2. Lista de materiales: material, unidades, precio_unitario, precio_total
            
            Devuelve el resultado como un objeto JSON con la siguiente estructura:
            {{
                "datos_proyecto": {{
                    "nombre_proyecto": "string",
                    "cliente": "string",
                    "celular": "string",
                    "telefono_fijo": "string",
                    "direccion": "string",
                    "email": "string",
                    "fecha": "string", 
                    "orden_trabajo": "string",
                    "total_materiales": "number",
                    "total_mano_obra": "number",
                    "total_proyecto": "number"
                }},
                "materiales": [
                    {{
                        "material": "string",
                        "unidades": "string",
                        "precio_unitario": "number",
                        "precio_total": "number"
                    }}
                ]
            }}
            """
            
            # Llamar a la API de OpenAI con el cliente actualizado
            client = openai.OpenAI(api_key=self.api_key)
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=1000,
                temperature=0.2
            )
            
            # Extraer el texto de la respuesta
            result = response.choices[0].text.strip()
            
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
        
        except Exception as e:
            logger.error(f"Error al realizar llamada directa a la API: {str(e)}")
            return {}
    
    # La función generate_summary ha sido eliminada por estar deshabilitada y no ser utilizada 