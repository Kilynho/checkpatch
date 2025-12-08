#!/usr/bin/env python3
"""
test_i18n.py - Tests for the internationalization system
"""

import unittest
import sys
from pathlib import Path

# Add the current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import i18n


class TestI18n(unittest.TestCase):
    """Test cases for i18n module."""
    
    def setUp(self):
        """Reset language to Spanish before each test."""
        i18n.set_language('es')
    
    def test_default_language_loaded_on_init(self):
        """Verify default language strings are loaded on initialization."""
        # Create a new LocaleManager instance to test initialization
        import importlib
        importlib.reload(i18n)
        # After reload, strings should be loaded
        text = i18n.get_text('html.dashboard_title')
        self.assertNotEqual(text, '[MISSING: html.dashboard_title]')
        self.assertEqual(text, 'Checkpatch Dashboard')
    
    def test_set_language_spanish(self):
        """Verify Spanish language can be set."""
        i18n.set_language('es')
        self.assertEqual(i18n.get_language(), 'es')
    
    def test_set_language_english(self):
        """Verify English language can be set."""
        i18n.set_language('en')
        self.assertEqual(i18n.get_language(), 'en')
    
    def test_get_text_spanish(self):
        """Verify Spanish text retrieval."""
        i18n.set_language('es')
        text = i18n.get_text('html.dashboard_title')
        self.assertEqual(text, 'Checkpatch Dashboard')
        
        text = i18n.get_text('html.global_summary')
        self.assertEqual(text, 'Resumen global')
    
    def test_get_text_english(self):
        """Verify English text retrieval."""
        i18n.set_language('en')
        text = i18n.get_text('html.dashboard_title')
        self.assertEqual(text, 'Checkpatch Dashboard')
        
        text = i18n.get_text('html.global_summary')
        self.assertEqual(text, 'Global Summary')
    
    def test_get_text_with_placeholders_spanish(self):
        """Verify Spanish text with placeholders."""
        i18n.set_language('es')
        text = i18n.get_text('analyzer.analyzing', total=100, workers=4)
        self.assertEqual(text, 'Analizando 100 archivos con 4 workers...')
        
        text = i18n.get_text('errors.file_not_exist', file='/test.c')
        self.assertEqual(text, 'No existe el archivo: /test.c')
    
    def test_get_text_with_placeholders_english(self):
        """Verify English text with placeholders."""
        i18n.set_language('en')
        text = i18n.get_text('analyzer.analyzing', total=100, workers=4)
        self.assertEqual(text, 'Analyzing 100 files with 4 workers...')
        
        text = i18n.get_text('errors.file_not_exist', file='/test.c')
        self.assertEqual(text, 'File does not exist: /test.c')
    
    def test_missing_key(self):
        """Verify missing key returns error message."""
        i18n.set_language('es')
        text = i18n.get_text('nonexistent.key')
        self.assertEqual(text, '[MISSING: nonexistent.key]')
    
    def test_missing_placeholder(self):
        """Verify missing placeholder returns error message."""
        i18n.set_language('es')
        # analyzer.analyzing requires 'total' and 'workers'
        text = i18n.get_text('analyzer.analyzing', total=100)  # missing 'workers'
        self.assertIn('[FORMAT_ERROR:', text)
    
    def test_get_available_languages(self):
        """Verify available languages are listed."""
        langs = i18n.get_available_languages()
        self.assertIn('es', langs)
        self.assertIn('en', langs)
        self.assertEqual(len(langs), 2)
    
    def test_shorthand_underscore(self):
        """Verify the underscore shorthand works."""
        from i18n import get_text as _
        
        i18n.set_language('es')
        text = _('html.global_summary')
        self.assertEqual(text, 'Resumen global')
        
        i18n.set_language('en')
        text = _('html.global_summary')
        self.assertEqual(text, 'Global Summary')
    
    def test_html_titles(self):
        """Verify HTML titles in both languages."""
        i18n.set_language('es')
        self.assertEqual(i18n.get_text('html.analyzer_title'), 'Informe Checkpatch Analyzer')
        self.assertEqual(i18n.get_text('html.autofix_title'), 'Informe Checkpatch Autofix')
        self.assertEqual(i18n.get_text('html.compile_title'), 'Informe de Compilación')
        
        i18n.set_language('en')
        self.assertEqual(i18n.get_text('html.analyzer_title'), 'Checkpatch Analyzer Report')
        self.assertEqual(i18n.get_text('html.autofix_title'), 'Checkpatch Autofix Report')
        self.assertEqual(i18n.get_text('html.compile_title'), 'Compilation Report')
    
    def test_console_messages(self):
        """Verify console messages in both languages."""
        i18n.set_language('es')
        self.assertEqual(
            i18n.get_text('analyzer.analysis_complete'),
            '✔ Análisis terminado.'
        )
        
        i18n.set_language('en')
        self.assertEqual(
            i18n.get_text('analyzer.analysis_complete'),
            '✔ Analysis complete.'
        )
    
    def test_error_messages(self):
        """Verify error messages in both languages."""
        i18n.set_language('es')
        self.assertIn('No se encontraron archivos', 
                     i18n.get_text('errors.files_not_found', extensions=['.c', '.h']))
        
        i18n.set_language('en')
        self.assertIn('No files found', 
                     i18n.get_text('errors.files_not_found', extensions=['.c', '.h']))


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
