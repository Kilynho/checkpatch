# analyze_core.py
"""
Funciones principales para análisis de checkpatch
"""

import subprocess
from pathlib import Path
from collections import defaultdict, Counter
from checkpatch_common import run_checkpatch

# Variables globales para el análisis
summary = defaultdict(lambda: {"correct": [], "warnings": [], "errors": []})
global_counts = {"correct": 0, "warnings": 0, "errors": 0}
error_reasons = Counter()
warning_reasons = Counter()
error_reason_files = defaultdict(list)
warning_reason_files = defaultdict(list)

FUNCTIONALITY_MAP = {
    "drivers": "Drivers",
    "fs": "Filesystems",
    "net": "Networking",
    "kernel": "Core Kernel",
    "arch": "Architecture",
    "lib": "Libraries",
    "include": "Headers",
}


def classify_functionality(file_path):
    """Clasifica un archivo según su funcionalidad."""
    parts = Path(file_path).parts
    for key, label in FUNCTIONALITY_MAP.items():
        if key in parts:
            return label
    return "Other"


def analyze_file(file_path, checkpatch_script):
    """
    Analiza un archivo con checkpatch y actualiza las estructuras globales.
    Retorna (errors, warnings, is_correct)
    """
    errors, warnings = run_checkpatch(file_path, checkpatch_script)
    
    functionality = classify_functionality(file_path)
    
    if errors:
        summary[functionality]["errors"].append(str(file_path))
        global_counts["errors"] += len(errors)
        for err in errors:
            msg = err["message"].replace("ERROR: ", "")
            error_reasons[msg] += 1
            error_reason_files[msg].append((str(file_path), err["line"]))
    
    if warnings:
        summary[functionality]["warnings"].append(str(file_path))
        global_counts["warnings"] += len(warnings)
        for warn in warnings:
            msg = warn["message"].replace("WARNING: ", "")
            warning_reasons[msg] += 1
            warning_reason_files[msg].append((str(file_path), warn["line"]))
    
    is_correct = not errors and not warnings
    if is_correct:
        summary[functionality]["correct"].append(str(file_path))
        global_counts["correct"] += 1
    
    return errors, warnings, is_correct


def get_analysis_summary():
    """Retorna resumen del análisis."""
    return {
        "summary": dict(summary),
        "global_counts": dict(global_counts),
        "error_reasons": dict(error_reasons),
        "warning_reasons": dict(warning_reasons),
        "error_reason_files": dict(error_reason_files),
        "warning_reason_files": dict(warning_reason_files),
    }


def reset_analysis():
    """Resetea las estructuras globales de análisis."""
    global summary, global_counts, error_reasons, warning_reasons
    global error_reason_files, warning_reason_files
    
    summary.clear()
    global_counts = {"correct": 0, "warnings": 0, "errors": 0}
    error_reasons.clear()
    warning_reasons.clear()
    error_reason_files.clear()
    warning_reason_files.clear()
