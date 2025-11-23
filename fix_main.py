# fix_main.py
"""
Módulo principal para aplicar fixes
"""

from fixes_core import *
from fix_utils import *
from fix_report import *
from fix_constants import (
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
    "char * array declaration might be better as static const": fix_char_array_static_const,
    "Prefer 'unsigned int' to bare use of 'unsigned'": BARE_UNSIGNED,
    "Improper SPDX comment style for '/home/kilynho/src/kernel/linux/init/initramfs_internal.h', please use '/*' instead": fix_spdx_comment,
    "externs should be avoided in .c files": fix_extern_in_c,
    "simple_strtoul is obsolete, use kstrtoul instead": SIMPLE_STRTOUL,
    "simple_strtol is obsolete, use kstrtol instead": SIMPLE_STRTOL,
    "Symbolic permissions 'S_IRUSR | S_IWUSR' are not preferred. Consider using octal permissions '0600'.": fix_symbolic_permissions,
    "Prefer [subsystem eg: netdev]_notice([subsystem]dev, ... then dev_notice(dev, ... then pr_notice(...  to printk(KERN_NOTICE ...": fix_prefer_notice,
    "Prefer [subsystem eg: netdev]_info([subsystem]dev, ... then dev_info(dev, ... then pr_info(... to printk(KERN_INFO ...": fix_printk_info,
    "Prefer [subsystem eg: netdev]_err([subsystem]dev, ... then dev_err(dev, ... then pr_err(... to printk(KERN_ERR ...": fix_printk_err,
    "Prefer [subsystem eg: netdev]_warn([subsystem]dev, ... then dev_warn(dev, ... then pr_warn(... to printk(KERN_WARNING ...": fix_printk_warn,
    "Prefer [subsystem eg: netdev]_dbg([subsystem]dev, ... then dev_dbg(dev, ... then pr_debug(... to printk(KERN_DEBUG ...": fix_printk_debug,
    "Use #include <linux/io.h> instead of <asm/io.h>": fix_asm_includes,
    "msleep < 20ms can sleep for up to 20ms; see function description of msleep().": fix_msleep_too_small,
    "kmalloc(x) without GFP flag": fix_kmalloc_no_flag,
    "Prefer strscpy over strcpy - see: https://github.com/KSPP/linux/issues/88": fix_memcpy_literal,
    "Prefer using strscpy instead of strncpy": fix_strncpy,
    "of_property_read without check": fix_of_read_no_check,
    "switch and case should be at the same indent": fix_switch_case_indent,
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

