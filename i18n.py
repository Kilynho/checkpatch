#!/usr/bin/env python3
"""
i18n.py - Sistema de internacionalización (i18n) para checkpatch

Proporciona soporte multiidioma mediante archivos JSON de localización.
"""

import json
import os
import sys
from pathlib import Path


class LocaleManager:
    """Gestor de localización singleton para toda la aplicación."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.current_language = "es"  # Idioma por defecto: español
            self.strings = {}
            self.i18n_dir = Path(__file__).parent / "i18n"
            self._initialized = True
            # Load default language strings on initialization
            self._load_strings()
    
    def set_language(self, language_code):
        """
        Establece el idioma activo y carga las cadenas correspondientes.
        
        Args:
            language_code: Código de idioma (ej: 'es', 'en')
        """
        self.current_language = language_code
        self._load_strings()
    
    def _load_strings(self):
        """Carga las cadenas del archivo de idioma actual."""
        lang_file = self.i18n_dir / f"{self.current_language}.json"
        
        if not lang_file.exists():
            # Fallback a español si el idioma no existe
            # Use stderr to avoid circular import with logger
            sys.stderr.write(f"[i18n WARNING] Language file not found: {lang_file}\n")
            if self.current_language != "es":
                self.current_language = "es"
                lang_file = self.i18n_dir / "es.json"
        
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.strings = json.load(f)
        except Exception as e:
            # Use stderr to avoid circular import with logger
            sys.stderr.write(f"[i18n ERROR] Failed to load language file {lang_file}: {e}\n")
            self.strings = {}
    
    def get(self, key, **kwargs):
        """
        Obtiene una cadena localizada por su clave.
        
        Args:
            key: Clave de la cadena (puede usar notación punto: 'section.key')
            **kwargs: Parámetros para formatear la cadena
            
        Returns:
            Cadena localizada y formateada
        """
        # Navegar por la estructura JSON usando notación punto
        parts = key.split('.')
        value = self.strings
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                # Si no se encuentra la clave, retornar la clave misma como fallback
                return f"[MISSING: {key}]"
        
        # Si es un string, formatear con los parámetros
        if isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError as e:
                return f"[FORMAT_ERROR: {key} - missing param {e}]"
        
        return value
    
    def get_language(self):
        """Retorna el código del idioma actual."""
        return self.current_language
    
    def get_available_languages(self):
        """Retorna lista de idiomas disponibles."""
        if not self.i18n_dir.exists():
            return []
        
        langs = []
        for file in self.i18n_dir.glob("*.json"):
            langs.append(file.stem)
        return sorted(langs)


# Instancia global singleton
_locale_manager = LocaleManager()


def set_language(language_code):
    """
    Establece el idioma de la aplicación.
    
    Args:
        language_code: Código de idioma (ej: 'es', 'en')
    """
    _locale_manager.set_language(language_code)


def get_text(key, **kwargs):
    """
    Obtiene texto localizado.
    
    Args:
        key: Clave del texto (notación punto: 'section.key')
        **kwargs: Parámetros para formatear el texto
        
    Returns:
        Texto localizado
    """
    return _locale_manager.get(key, **kwargs)


def get_language():
    """Retorna el idioma actual."""
    return _locale_manager.get_language()


def get_available_languages():
    """Retorna lista de idiomas disponibles."""
    return _locale_manager.get_available_languages()


# Alias corto para conveniencia
_ = get_text
