# utils.py
"""
Funciones helper para lectura/escritura de archivos
y utilidades generales
"""

from pathlib import Path
import shutil

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
