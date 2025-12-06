# utils.py
"""
Funciones helper para lectura/escritura de archivos,
utilidades de checkpatch y constantes comunes
"""

from pathlib import Path
import shutil
import subprocess
import os
import re

# ============================
# Mapeos y configuración
# ============================
FUNCTIONALITY_MAP = {
    "drivers": "Drivers",
    "fs": "Filesystems",
    "net": "Networking",
    "kernel": "Core Kernel",
    "arch": "Architecture",
    "lib": "Libraries",
    "include": "Headers",
}

EXTENSIONS = [".c", ".h"]
MAX_WORKERS = 4

# ============================
# CSS común para HTML
# ============================
COMMON_CSS = """
body { font-family: Arial, Helvetica, sans-serif; padding: 20px; }
h1 { display:flex; justify-content:space-between; align-items:center; }
table { border-collapse: collapse; margin-bottom: 20px; width: 100%; }
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; width: 100%; }
th { background: #eee; }
.correct { color: green; font-weight: bold; }
.warnings { color: orange; font-weight: bold; }
.errors { color: red; font-weight: bold; }
h3.errors, h4.errors { color: #d32f2f; background: #ffebee; padding: 10px; border-left: 4px solid #d32f2f; border-radius: 4px; }
h3.warnings, h4.warnings { color: #f57c00; background: #fff3e0; padding: 10px; border-left: 4px solid #f57c00; border-radius: 4px; }
.total { font-weight: bold; color: #2196F3; }
.skipped { color: #757575; font-weight: bold; }
details { margin-bottom: 8px; }
pre { background: #f4f4f4; padding: 8px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; }
.bar { display: inline-block; height: 12px; background: #ddd; border-radius: 3px; width: 100%; overflow: hidden; }
.bar-inner { height: 100%; border-radius: 3px; }
.bar-errors { background: #e57373; }
.bar-warnings { background: #ffb74d; }
.bar-correct { background: #81c784; }
.bar-total { background: #2196F3; }
th.num, td.num { text-align: center; width: 110px; }

/* Per-file detail styling */
details.file-detail { margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; overflow: hidden; }
details.file-detail summary { cursor: pointer; padding: 12px; background: #f9f9f9; font-weight: bold; color: #2196F3; user-select: none; display: flex; justify-content: space-between; align-items: center; }
details.file-detail summary:hover { background: #f0f0f0; }
.detail-content { padding: 12px; background: white; }
.stats { display: flex; gap: 20px; align-items: center; margin-left: auto; }
.stat-item { display: flex; align-items: center; gap: 4px; }
.added { color: #4CAF50; font-weight: bold; }
.removed { color: #f44336; font-weight: bold; }
.fixed-badge { background: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: normal; }
.skipped-badge { background: #757575; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: normal; }
.diff-pre { background:#f5f5f5; padding:12px; border-radius:4px; overflow-x:auto; font-size:11px; line-height:1.4; border-left:3px solid #2196F3; }
"""

# ============================
# Funciones de lectura/escritura
# ============================

def _read_lines_and_idx(file_path, line_number):
    with open(file_path, "r") as f:
        lines = f.readlines()
    idx = line_number - 1
    return lines, idx

def _write_lines(file_path, lines):
    with open(file_path, "w") as f:
        f.writelines(lines)

def backup_read(file_path, line_number):
    """
    Hace backup del archivo y lee todas las líneas. Devuelve (lines, idx, line) para la línea solicitada.
    """
    file_path = Path(file_path)
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    if not backup_path.exists():
        shutil.copy2(file_path, backup_path)
    lines, idx = _read_lines_and_idx(file_path, line_number)
    if idx < 0 or idx >= len(lines):
        return False
    line = lines[idx]
    return lines, idx, line

def apply_line_transform(file_path, line_number, transform_fn):
    """Read its lines, call transform_fn(line) which should
    return a new line (string) or None if no change should be made. If the
    returned line is different, write back and return True. Otherwise return False.
    """
    lines, idx = _read_lines_and_idx(file_path, line_number)
    if idx < 0 or idx >= len(lines):
        return False
    line = lines[idx]
    new_line = transform_fn(line)
    if new_line is None:
        return False
    if new_line != line:
        lines[idx] = new_line
        _write_lines(file_path, lines)
        return True
    return False


def apply_lines_callback(file_path, line_number, callback_fn):
    """Backup the file, read all lines, call callback_fn(lines, idx).
    The callback should perform any in-memory modifications to `lines` and
    return True if the file should be written back, or False otherwise.
    Returns True if changes were written, False otherwise.
    """
    lines, idx = _read_lines_and_idx(file_path, line_number)
    changed = callback_fn(lines, idx)
    if changed:
        _write_lines(file_path, lines)
        return True
    return False

def apply_pattern_replace(file_path, line_number, pattern, replacement, use_regex=False, condition=None):
    """
    Aplica un reemplazo de patrón genérico.
    - pattern: patrón a buscar
    - replacement: texto/patrón de reemplazo
    - use_regex: si True, usa re.sub; si False, usa str.replace
    - condition: función opcional que verifica si debe aplicarse (recibe la línea)
    """
    import re as regex_module
    def transform(line):
        if condition and not condition(line):
            return None
        if use_regex:
            new_line = regex_module.sub(pattern, replacement, line)
        else:
            new_line = line.replace(pattern, replacement)
        return new_line if new_line != line else None
    return apply_line_transform(file_path, line_number, transform)

# ============================
# Funciones comunes checkpatch
# ============================

def run_checkpatch(file_path, checkpatch_script, kernel_dir=None):
    """
    Ejecuta checkpatch.pl sobre un archivo y retorna errors, warnings y output completo.
    Retorna (error_list, warning_list, full_output) donde cada item es {"line": N, "message": "..."}
    """
    try:
        # Si tenemos kernel_dir, usar ruta relativa para que checkpatch la muestre correctamente
        if kernel_dir:
            rel_path = os.path.relpath(file_path, kernel_dir)
            result = subprocess.run(
                ["perl", checkpatch_script, "--no-tree", "--file", rel_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(kernel_dir)
            )
        else:
            result = subprocess.run(
                ["perl", checkpatch_script, "--no-tree", "--file", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
        
        full_output = result.stdout
        errors = []
        warnings = []
        
        lines_list = result.stdout.split("\n")
        i = 0
        while i < len(lines_list):
            line = lines_list[i].strip()
            
            # Formato sin --terse:
            # WARNING: message
            # #line: FILE: path:line:
            # + code
            
            if line.startswith("ERROR: "):
                message = line
                line_num = 0
                # Buscar siguiente línea con #N: FILE:
                if i + 1 < len(lines_list):
                    next_line = lines_list[i + 1].strip()
                    if next_line.startswith("#") and "FILE:" in next_line:
                        try:
                            # Extraer número de línea de FILE: path:NUM:
                            file_part = next_line.split("FILE:")[1].strip()
                            line_num = int(file_part.split(":")[-2])
                        except (IndexError, ValueError):
                            pass
                errors.append({"line": line_num, "message": message})
                i += 1
                
            elif line.startswith("WARNING: "):
                message = line
                line_num = 0
                # Buscar siguiente línea con #N: FILE:
                if i + 1 < len(lines_list):
                    next_line = lines_list[i + 1].strip()
                    if next_line.startswith("#") and "FILE:" in next_line:
                        try:
                            # Extraer número de línea de FILE: path:NUM:
                            file_part = next_line.split("FILE:")[1].strip()
                            line_num = int(file_part.split(":")[-2])
                        except (IndexError, ValueError):
                            pass
                warnings.append({"line": line_num, "message": message})
                i += 1
                
            else:
                i += 1
        
        return errors, warnings, full_output
    
    except subprocess.TimeoutExpired:
        return [], [], ""
    except Exception:
        return [], [], ""


def find_source_files(directory, extensions=[".c", ".h"]):
    """
    Encuentra todos los archivos de código fuente en un directorio.
    """
    files = []
    for ext in extensions:
        files.extend(Path(directory).rglob(f"*{ext}"))
    return sorted(files)


def display_path(file_path, base_dir=None):
    """
    Muestra una ruta de archivo de forma relativa.
    """
    try:
        if base_dir:
            return os.path.relpath(file_path, base_dir)
        return str(file_path)
    except (ValueError, TypeError):
        return str(file_path)


def percentage(value, total):
    """Calcula porcentaje."""
    return f"{(value / total * 100):.1f}%" if total > 0 else "0%"


def percentage_value(value, total):
    """Calcula valor numérico de porcentaje (sin %)."""
    return (value / total * 100) if total > 0 else 0


def bar_width(value, total, max_width=200):
    """Calcula ancho de barra para visualización."""
    return int(value / total * max_width) if total > 0 else 0
