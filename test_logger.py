#!/usr/bin/env python3
"""
Unit tests for the logger module.
"""

import unittest
import logging
import tempfile
import os
from pathlib import Path
import sys

# Añadir directorio raíz al path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import logger


class TestLogger(unittest.TestCase):
    """Tests para el sistema de logging."""
    
    def setUp(self):
        """Configuración antes de cada test."""
        # Resetear el logger para cada test
        logger._logger_instance._initialized = False
        logger._logger_instance.__init__()
    
    def test_logger_singleton(self):
        """Verificar que el logger es singleton."""
        logger1 = logger.CheckpatchLogger()
        logger2 = logger.CheckpatchLogger()
        self.assertIs(logger1, logger2, "Logger should be singleton")
    
    def test_setup_logging_default(self):
        """Verificar configuración default del logging."""
        logger.setup_logging()
        # El logger debería estar configurado
        self.assertIsNotNone(logger._logger_instance.console_handler)
        self.assertIsNone(logger._logger_instance.file_handler)
    
    def test_setup_logging_with_file(self):
        """Verificar configuración con archivo de log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger.setup_logging(log_file=str(log_file))
            
            # Escribir mensaje de prueba
            logger.info("Test message")
            
            # Verificar que el archivo existe y contiene el mensaje
            self.assertTrue(log_file.exists(), "Log file should exist")
            content = log_file.read_text()
            self.assertIn("Test message", content)
            self.assertIn("INFO", content)
    
    def test_log_levels(self):
        """Verificar que los diferentes niveles funcionan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            # Configurar con nivel DEBUG
            logger.setup_logging(level=logging.DEBUG, log_file=str(log_file))
            
            # Escribir mensajes de diferentes niveles
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
            
            # Verificar que todos aparecen en el archivo
            content = log_file.read_text()
            self.assertIn("Debug message", content)
            self.assertIn("Info message", content)
            self.assertIn("Warning message", content)
            self.assertIn("Error message", content)
            self.assertIn("Critical message", content)
    
    def test_get_level_from_string(self):
        """Verificar conversión de string a nivel de logging."""
        self.assertEqual(logger.get_level_from_string("DEBUG"), logging.DEBUG)
        self.assertEqual(logger.get_level_from_string("INFO"), logging.INFO)
        self.assertEqual(logger.get_level_from_string("WARNING"), logging.WARNING)
        self.assertEqual(logger.get_level_from_string("ERROR"), logging.ERROR)
        self.assertEqual(logger.get_level_from_string("CRITICAL"), logging.CRITICAL)
        
        # Verificar case-insensitive
        self.assertEqual(logger.get_level_from_string("debug"), logging.DEBUG)
        self.assertEqual(logger.get_level_from_string("info"), logging.INFO)
        
        # Verificar default para valores desconocidos
        self.assertEqual(logger.get_level_from_string("UNKNOWN"), logging.INFO)
    
    def test_colored_formatter(self):
        """Verificar que el formateador con colores funciona."""
        formatter = logger.ColoredFormatter(use_colors=True)
        
        # Crear un LogRecord de prueba
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="[TEST] Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        # Debería contener el mensaje
        self.assertIn("[TEST] Test message", formatted)
    
    def test_colored_formatter_no_colors(self):
        """Verificar formateador sin colores."""
        formatter = logger.ColoredFormatter(use_colors=False)
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        self.assertEqual(formatted, "Test message")
        # No debería contener códigos ANSI
        self.assertNotIn("\033[", formatted)
    
    def test_log_file_creates_directory(self):
        """Verificar que se crean directorios para el archivo de log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "subdir" / "logs" / "test.log"
            
            # El directorio subdir/logs no existe aún
            self.assertFalse(log_file.parent.exists())
            
            # Configurar logging con este archivo
            logger.setup_logging(log_file=str(log_file))
            logger.info("Test")
            
            # Ahora el directorio y archivo deberían existir
            self.assertTrue(log_file.parent.exists())
            self.assertTrue(log_file.exists())


def run_tests():
    """Ejecutar los tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestLogger)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
