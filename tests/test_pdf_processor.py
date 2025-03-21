#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for the PDF processor
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to enable imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pdf_processor import PDFProcessor
from src.utils import clean_text, extract_currency, is_estimate_item


class TestPDFProcessor(unittest.TestCase):
    """Test cases for the PDF processor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data_dir = Path(__file__).parent / "data"
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Create a mock PDF path
        self.mock_pdf_path = self.test_data_dir / "test_estimate.pdf"
        
        # Create a mock processor
        self.processor = PDFProcessor(self.mock_pdf_path)
        
        # Mock the pages attribute
        self.processor.pages = [MagicMock(), MagicMock()]
    
    @patch('src.pdf_processor.convert_from_path')
    def test_convert_pdf_to_images(self, mock_convert):
        """Test converting PDF to images"""
        # Configure the mock
        mock_pages = [MagicMock(), MagicMock()]
        mock_convert.return_value = mock_pages
        
        # Call the method
        self.processor._convert_pdf_to_images()
        
        # Check if the convert_from_path was called with correct arguments
        mock_convert.assert_called_once()
        self.assertEqual(self.processor.pages, mock_pages)
    
    @patch('src.pdf_processor.pytesseract.image_to_string')
    def test_extract_text_from_images(self, mock_image_to_string):
        """Test extracting text from images"""
        # Configure the mock
        mock_image_to_string.side_effect = ["Page 1 text", "Page 2 text"]
        
        # Call the method
        self.processor._extract_text_from_images()
        
        # Check if image_to_string was called for each page
        self.assertEqual(mock_image_to_string.call_count, 2)
        
        # Check if the text content was updated correctly
        self.assertIn("Page 1 text", self.processor.text_content)
        self.assertIn("Page 2 text", self.processor.text_content)
    
    def test_extract_metadata(self):
        """Test extracting metadata from text content"""
        # Set up test text content
        self.processor.text_content = """
        Proyecto: Edificio Residencial Las Flores
        Cliente: Inmobiliaria XYZ
        Fecha: 15/03/2025
        Ubicación: Calle Principal 123, Ciudad
        Total: $1,500,000.00
        """
        
        # Call the method
        self.processor._extract_metadata()
        
        # Check if metadata was extracted correctly
        metadata = self.processor.extracted_data["metadata"]
        self.assertEqual(metadata["project_name"], "Edificio Residencial Las Flores")
        self.assertEqual(metadata["client"], "Inmobiliaria XYZ")
        self.assertEqual(metadata["date"], "15/03/2025")
        self.assertEqual(metadata["location"], "Calle Principal 123, Ciudad")
        self.assertEqual(metadata["total_amount"], "1,500,000.00")


class TestUtils(unittest.TestCase):
    """Test cases for utility functions"""
    
    def test_clean_text(self):
        """Test cleaning and normalizing text"""
        # Test with multiple spaces and newlines
        input_text = "This   is  a\n\ntest   text"
        expected = "This is a test text"
        self.assertEqual(clean_text(input_text), expected)
        
        # Test with unicode characters
        input_text = "Café Ñandú"
        expected = "Cafe Nandu"  # Normalized
        self.assertEqual(clean_text(input_text), expected)
    
    def test_extract_currency(self):
        """Test extracting currency from text"""
        # Test with dollar sign
        self.assertEqual(extract_currency("Price: $123.45"), 123.45)
        
        # Test with comma in number
        self.assertEqual(extract_currency("Total: $1,234.56"), 1234.56)
        
        # Test without currency symbol
        self.assertEqual(extract_currency("Amount: 789.10"), 789.10)
        
        # Test with no currency
        self.assertIsNone(extract_currency("No currency here"))
    
    def test_is_estimate_item(self):
        """Test identifying estimate items"""
        # Test with code at beginning
        self.assertTrue(is_estimate_item("A101 Excavation work"))
        
        # Test with description and measurement
        self.assertTrue(is_estimate_item("Foundation concrete m³ 75 $1,200.00"))
        
        # Test with non-estimate text
        self.assertFalse(is_estimate_item("This is just regular text"))


if __name__ == "__main__":
    unittest.main() 