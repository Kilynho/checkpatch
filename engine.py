# engine.py
"""
Módulo principal para aplicar fixes
"""

from core import *
from utils import *
from report import *
from constants import (
    SPACE_AFTER_COMMA,
    SPACE_BEFORE_COMMA,
    SPACE_BEFORE_PAREN,
    SPACES_AROUND_EQUALS,
    SPACE_AFTER_OPEN_PAREN,
    SPACE_BEFORE_TABS,
    BARE_UNSIGNED,
    SIMPLE_STRTOUL,
    SIMPLE_STRTOL,
)

# Mapeo de reglas a funciones o tuplas (pattern, replacement, use_regex, condition)
# Para funciones complejas, usar None como valor y definir la función en fixes_core.py
AUTO_FIX_RULES = {
    "Missing a blank line after declarations": fix_missing_blank_line,
    "quoted string split across lines": fix_quoted_string_split,
    "space required after that ','": SPACE_AFTER_COMMA,
    "space prohibited before that ','": SPACE_BEFORE_COMMA,
    "space prohibited before that close parenthesis ')'": SPACE_BEFORE_PAREN,
    "spaces required around that '='": SPACES_AROUND_EQUALS,
    "code indent should use tabs where possible": fix_indent_tabs,
    "trailing whitespace": fix_trailing_whitespace,
    "do not use assignment in if condition": fix_assignment_in_if,
    "Use of const init definition must use __initconst": fix_initconst,
    "space prohibited after that open parenthesis '('": SPACE_AFTER_OPEN_PAREN,
    "space before tabs": SPACE_BEFORE_TABS,
    "void function return statements are not generally useful": fix_void_return,
    "braces {} are not necessary for single statement blocks": fix_unnecessary_braces,
    "Block comments use a trailing */ on a separate line": fix_block_comment_trailing,
    # TODO: PROBLEMATIC - Generates invalid code (const static const)
    # "char * array declaration might be better as static const": fix_char_array_static_const,
    "Prefer 'unsigned int' to bare use of 'unsigned'": BARE_UNSIGNED,
    "Improper SPDX comment style for '/home/kilynho/src/kernel/linux/init/initramfs_internal.h', please use '/*' instead": fix_spdx_comment,
    "externs should be avoided in .c files": fix_extern_in_c,
    "simple_strtoul is obsolete, use kstrtoul instead": SIMPLE_STRTOUL,
    "simple_strtol is obsolete, use kstrtol instead": SIMPLE_STRTOL,
    "Symbolic permissions 'S_IRUSR | S_IWUSR' are not preferred. Consider using octal permissions '0600'.": fix_symbolic_permissions,
    "Prefer [subsystem eg: netdev]_notice([subsystem]dev, ... then dev_notice(dev, ... then pr_notice(...  to printk(KERN_NOTICE ...": fix_prefer_notice,
    "Prefer [subsystem eg: netdev]_info([subsystem]dev, ... then dev_info(dev, ... then pr_info(...  to printk(KERN_INFO ...": fix_printk_info,
    "Prefer [subsystem eg: netdev]_err([subsystem]dev, ... then dev_err(dev, ... then pr_err(...  to printk(KERN_ERR ...": fix_printk_err,
    "Prefer [subsystem eg: netdev]_warn([subsystem]dev, ... then dev_warn(dev, ... then pr_warn(...  to printk(KERN_WARNING ...": fix_printk_warn,
    "Prefer [subsystem eg: netdev]_dbg([subsystem]dev, ... then dev_dbg(dev, ... then pr_debug(...  to printk(KERN_DEBUG ...": fix_printk_debug,
    "Prefer [subsystem eg: netdev]_emerg([subsystem]dev, ... then dev_emerg(dev, ... then pr_emerg(...  to printk(KERN_EMERG ...": fix_printk_emerg,
    # TODO: PROBLEMATIC - Adds KERN_CONT instead of correct level (KERN_INFO, KERN_ERR, etc)
    # "printk() should include KERN_<LEVEL> facility level": fix_printk_kern_level,
    "Comparing jiffies is almost always wrong; prefer time_after, time_before and friends": fix_jiffies_comparison,
    # TODO: PROBLEMATIC - Replaces strings incorrectly, breaks logging messages
    # "Prefer using": fix_func_name_in_string,  # Matches "Prefer using '\"%%s...\", __func__'"
    "else is not generally useful after a break or return": fix_else_after_return,
    "Prefer __weak over __attribute__((weak))": fix_weak_attribute,
    "Possible unnecessary 'out of memory' message": fix_oom_message,
    "Use #include <linux/io.h> instead of <asm/io.h>": fix_asm_includes,
    "Use #include <linux/cacheflush.h> instead of <asm/cacheflush.h>": fix_asm_includes,
    "__initdata should be placed after": fix_initdata_placement,
    "Missing or malformed SPDX-License-Identifier tag in line 1": fix_missing_spdx,
    "msleep < 20ms can sleep for up to 20ms; see function description of msleep().": fix_msleep_too_small,
    "kmalloc(x) without GFP flag": fix_kmalloc_no_flag,
    "Prefer strscpy over strcpy - see: https://github.com/KSPP/linux/issues/88": fix_strcpy_to_strscpy,
    "Prefer using strscpy instead of strncpy": fix_strncpy,
    "of_property_read without check": fix_of_read_no_check,
    "switch and case should be at the same indent": fix_switch_case_indent,
    "Avoid logging continuation uses where feasible": fix_logging_continuation,
    "It's generally not useful to have the filename in the file": fix_filename_in_file,
    "please, no spaces at the start of a line": fix_spaces_at_start_of_line,
    "__FUNCTION__ is gcc specific, use __func__": fix_function_macro,
    "space required before the open brace '{'": fix_space_before_open_brace,
    "else should follow close brace '}'": fix_else_after_close_brace,
    "Prefer sizeof(*p) over sizeof(struct type)": fix_sizeof_struct,
    "Consecutive strings are generally better as a single string": fix_consecutive_strings,
    "Comparison to NULL could be written": fix_comparison_to_null,
    "Comparisons should place the constant on the right side": fix_constant_comparison,
}

def apply_fixes(file_path, issues):
    """
    Aplica fixes a un archivo y devuelve una lista de resultados estructurados.
    Cada resultado es un diccionario:
       {
         "type": "warning" | "error",
         "fixed": True/False,
         "message": "...",
         "line": N,
         "rule": "nombre_regla"
       }
    """

    # Unificar backup y lectura
    res = backup_read(file_path, 1)
    lines = res[0] if res else []
    results = []

    for issue in issues:
        line = issue.get("line")
        msg = issue.get("message")
        issue_type = issue.get("type", "warning")

        applied_rule = None
        fixed = False

        # Buscar regla aplicable
        for rule_key, rule_fn in AUTO_FIX_RULES.items():
            if rule_key in msg:
                applied_rule = rule_key
                try:
                    # Si es una tupla (pattern, replacement, use_regex, condition), usar helper genérico
                    if isinstance(rule_fn, tuple):
                        pattern, replacement, use_regex, condition = rule_fn
                        fixed = apply_pattern_replace(file_path, line, pattern, replacement, use_regex, condition)
                    else:
                        # Si es una función, llamarla directamente
                        fixed = rule_fn(file_path, line)
                except Exception as e:
                    fixed = False
                    applied_rule = f"{rule_key} (EXCEPTION: {e})"
                break

        # Resultado estructurado
        result = {
            "type": issue_type,
            "fixed": bool(fixed),
            "message": applied_rule if applied_rule else "No applicable fix",
            "line": line,
            "rule": applied_rule
        }

        results.append(result)

    return results


# ============================
# Funciones del Analyzer
# ============================

from collections import defaultdict, Counter
from pathlib import Path
from utils import run_checkpatch, FUNCTIONALITY_MAP

# Variables globales para el análisis
summary = defaultdict(lambda: {"correct": [], "warnings": [], "errors": []})
global_counts = {"correct": 0, "warnings": 0, "errors": 0}
error_reasons = Counter()
warning_reasons = Counter()
error_reason_files = defaultdict(list)
warning_reason_files = defaultdict(list)
file_outputs = {}  # Guarda el output completo de checkpatch por fichero
kernel_dir_path = ""  # Para calcular rutas relativas


def classify_functionality(file_path):
    """Clasifica un archivo según su funcionalidad."""
    parts = Path(file_path).parts
    for key, label in FUNCTIONALITY_MAP.items():
        if key in parts:
            return label
    return "Other"


def analyze_file(file_path, checkpatch_script, kernel_dir=None):
    """
    Analiza un archivo con checkpatch y actualiza las estructuras globales.
    Retorna (errors, warnings, is_correct)
    """
    global kernel_dir_path
    if kernel_dir:
        kernel_dir_path = kernel_dir
    
    errors, warnings, output = run_checkpatch(file_path, checkpatch_script, kernel_dir)
    
    functionality = classify_functionality(file_path)
    file_path_str = str(file_path)
    
    # Guardar output completo
    file_outputs[file_path_str] = output
    
    if errors:
        summary[functionality]["errors"].append(file_path_str)
        global_counts["errors"] += len(errors)
        for err in errors:
            msg = err["message"].replace("ERROR: ", "")
            error_reasons[msg] += 1
            error_reason_files[msg].append((file_path_str, err["line"]))
    
    if warnings:
        summary[functionality]["warnings"].append(file_path_str)
        global_counts["warnings"] += len(warnings)
        for warn in warnings:
            msg = warn["message"].replace("WARNING: ", "")
            warning_reasons[msg] += 1
            warning_reason_files[msg].append((file_path_str, warn["line"]))
    
    is_correct = not errors and not warnings
    if is_correct:
        summary[functionality]["correct"].append(file_path_str)
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
        "file_outputs": dict(file_outputs),
        "kernel_dir": kernel_dir_path,
    }


def reset_analysis():
    """Resetea las estructuras globales de análisis."""
    global summary, global_counts, error_reasons, warning_reasons
    global error_reason_files, warning_reason_files, file_outputs, kernel_dir_path
    
    summary.clear()
    global_counts = {"correct": 0, "warnings": 0, "errors": 0}
    error_reasons.clear()
    warning_reasons.clear()
    error_reason_files.clear()
    warning_reason_files.clear()
    file_outputs.clear()
    kernel_dir_path = ""

