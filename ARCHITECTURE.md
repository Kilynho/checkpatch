# Checkpatch System Architecture

Sistema unificado para análisis y corrección automática de warnings/errores de checkpatch.pl

## Estructura de Módulos

### main.py (300 líneas) ✨ Entry Point
**Punto de entrada único con dos modos de operación:**
- `--analyze`: Análisis paralelo de archivos con checkpatch.pl
- `--fix`: Aplicación automática de correcciones

**Características:**
- ThreadPoolExecutor para procesamiento paralelo
- Barra de progreso visual
- Manejo unificado de argumentos
- Compatible con flujo anterior (analyzer + autofix)

**Uso:**
```bash
./main.py --analyze --source-dir linux/init
./main.py --fix --json json/checkpatch.json
```

---

### common.py (147 líneas) 🔧 Shared Core
**Funciones y constantes compartidas entre analyzer y autofix.**

**Contenido:**
- `COMMON_CSS`: Estilos HTML unificados para reportes
- `FUNCTIONALITY_MAP`: Clasificación por subsistema kernel
- `EXTENSIONS`: Extensiones de archivos a procesar (`.c`, `.h`)
- `MAX_WORKERS`: Concurrencia para análisis paralelo
- `run_checkpatch()`: Ejecución de checkpatch.pl
- `find_source_files()`: Búsqueda recursiva de archivos
- `display_path()`: Rutas relativas para reportes
- `percentage()`, `bar_width()`: Utilidades para reportes HTML

---

### engine.py (209 líneas) ⚙️ Core Logic
**Lógica principal de análisis y corrección.**

#### Sección Autofix:
- `AUTO_FIX_RULES`: Mapeo de warnings/errores a funciones fix (en engine.py)
- `apply_fixes()`: Aplica correcciones y retorna resultados estructurados

**Reglas soportadas (40+):**
- Espaciado (comas, paréntesis, tabulaciones)
- Comentarios (SPDX, bloques)
- Strings (split across lines)
- Condicionales (assignment in if)
- Funciones obsoletas (simple_strtoul → kstrtoul)
- printk → pr_* / dev_*
- Permisos simbólicos → octales
- __initdata placement
- Y más...

#### Sección Analyzer:
- Variables globales: `summary`, `error_reasons`, `warning_reasons`
- `classify_functionality()`: Clasifica archivo por subsistema
- `analyze_file()`: Analiza archivo y actualiza estadísticas
- `get_analysis_summary()`: Retorna resumen completo
- `reset_analysis()`: Limpia estado global

---

### report.py (582 líneas) 📊 HTML Reports
**Generación de reportes HTML para analyzer y autofix.**

#### Sección Autofix:
- `generate_html_report()`: Reporte detallado de correcciones
  - Resumen global (corregidos vs saltados)
  - Desglose por motivo (errors y warnings)
  - Detalle por archivo con diffs coloreados
  - Estadísticas de líneas añadidas/eliminadas

- `summarize_results()`: Salida consola con estadísticas

#### Sección Analyzer:
- `generate_analyzer_html()`: Reporte de análisis inicial
  - Resumen global (correct, warnings, errors)
  - Resumen por motivo con lista de archivos
  - Resumen por funcionalidad (drivers, fs, net, etc.)

**Características HTML:**
- CSS unificado (COMMON_CSS)
- Barras de progreso visuales
- Diffs coloreados (+verde, -rojo)
- Tablas expandibles con <details>

---

### core.py (750 líneas) 🔨 Fix Implementations
**Implementaciones de todas las funciones de corrección.**

**Funciones destacadas:**
- `fix_missing_blank_line()`: Línea en blanco tras declaraciones
- `fix_quoted_string_split()`: Unifica strings multi-línea
- `fix_indent_tabs()`: Convierte espacios a tabs
- `fix_initdata_placement()`: Coloca `__initdata` correctamente
- `fix_missing_spdx()`: Añade SPDX-License-Identifier
- `fix_printk_*()`: Familia printk → pr_* / dev_*
- `fix_jiffies_comparison()`: jiffies → time_after/before
- `fix_strcpy_to_strscpy()`: strcpy → strscpy
- Y 30+ funciones más...

**Patrón común:**
```python
def fix_something(file_path, line_number):
    """Fix specific issue"""
    lines = read_file_lines(file_path)
    # Apply transformation
    write_file_lines(file_path, lines)
    return True  # Success
```

---

### utils.py (83 líneas) 🛠️ Utilities
**Funciones auxiliares para transformaciones de código.**

- `backup_read()`: Crea backup (.bak) y lee archivo
- `apply_line_transform()`: Aplica transformación a línea específica
- `apply_lines_callback()`: Aplica callback a rango de líneas
- `apply_pattern_replace()`: Reemplazo con regex o literal

---

### constants.py (54 líneas) 📝 Constants
**Constantes para transformaciones comunes (tuplas pattern/replacement).**

Ejemplos:
- `SPACE_AFTER_COMMA`: `(r',(\S)', r', \1', True, None)`
- `BARE_UNSIGNED`: `(r'\bunsigned\b\s*(?!int|long|short|char)', 'unsigned int ', True, None)`
- `SIMPLE_STRTOUL`: Regex para simple_strtoul → kstrtoul

---

### test.py (201 líneas) ✅ Integration Tests
**Suite de tests con unittest para VS Code.**

**Tests:**
- `test_full_integration()`: Análisis + autofix completo
- Verifica archivos modificados
- Valida estadísticas de correcciones
- Compatible con VS Code Test Explorer

**Uso:**
```bash
./test.py  # Ejecuta suite completa
```

---

## Flujo de Trabajo

### 1. Análisis (--analyze)
```
main.py
  ↓
find_source_files() → [archivos .c/.h]
  ↓
ThreadPoolExecutor → analyze_file() (paralelo)
  ↓
get_analysis_summary() → analysis_data
  ↓
generate_analyzer_html() → html/analyzer.html
  ↓
json.dump() → json/checkpatch.json
```

### 2. Autofix (--fix)
```
main.py
  ↓
json.load() → issues per file
  ↓
apply_fixes() → [results per issue]
  ↓
generate_html_report() → html/autofix.html
  ↓
summarize_results() → console output
```

### 3. Script ./run
```bash
#!/bin/bash
./main.py --analyze --source-dir linux/init
./main.py --fix --json json/checkpatch.json
```

---

## Estadísticas Actuales

**Archivos procesados:** 14 archivos en `linux/init/`

**Warnings detectados:** 36 warnings

**Tasa de corrección:** 85.4% (histórico: 129/151)

**Edge cases no implementados:**
- Logging continuation (`KERN_CONT`)
- `__func__` en algunos contextos
- Algunos casos complejos de printk

---

## Mejoras vs Sistema Original

### Antes:
- ❌ Nombres con prefijos: `checkpatch_`, `fix_`, `fixes_`, `test_`
- ❌ Módulos con guiones bajos: `checkpatch_common.py`, `fix_main.py`
- ❌ Nombres largos y redundantes

### Ahora:
- ✅ Nombres simples y claros: `main.py`, `engine.py`, `core.py`
- ✅ Sin prefijos ni guiones bajos innecesarios
- ✅ Estructura limpia: `common.py`, `report.py`, `utils.py`, `constants.py`, `test.py`
- ✅ Más fácil de recordar e importar

---

## Contribuciones

Para añadir nuevo fix:

1. Implementar función en `core.py`:
```python
def fix_new_issue(file_path, line_number):
    """Fix description"""
    # Implementation
    return True
```

2. Añadir regla a `AUTO_FIX_RULES` en `engine.py`:
```python
AUTO_FIX_RULES = {
    ...
    "new issue message": fix_new_issue,
}
```

3. Probar con `./test.py`

---

## Contacto

Sistema desarrollado por [@kilynho](https://github.com/kilynho)

Versión: 2.0 (Post-refactor unification)
