#!/usr/bin/env python3
"""
Analiza la cobertura real de tipos de checkpatch basándose en el JSON actual
"""

import json
import re
from collections import defaultdict
from engine import AUTO_FIX_RULES

# Mapeo manual de mensajes a tipos de checkpatch
# Basado en el código fuente de checkpatch.pl
MESSAGE_TO_TYPE = {
    "Missing a blank line after declarations": "LINE_SPACING",
    "quoted string split across lines": "SPLIT_STRING",
    "space required after that ','": "SPACING",
    "space prohibited before that ','": "SPACING",
    "space prohibited before that close parenthesis ')'": "SPACING",
    "spaces required around that '='": "SPACING",
    "code indent should use tabs where possible": "CODE_INDENT",
    "trailing whitespace": "TRAILING_WHITESPACE",
    "do not use assignment in if condition": "ASSIGN_IN_IF",
    "Use of const init definition must use __initconst": "MISPLACED_INIT",
    "space prohibited after that open parenthesis '('": "SPACING",
    "space before tabs": "SPACE_BEFORE_TAB",
    "void function return statements are not generally useful": "RETURN_VOID",
    "braces {} are not necessary for single statement blocks": "BRACES",
    "Block comments use a trailing */ on a separate line": "BLOCK_COMMENT_STYLE",
    "char * array declaration might be better as static const": "STATIC_CONST_CHAR_ARRAY",
    "Prefer 'unsigned int' to bare use of 'unsigned'": "UNSPECIFIED_INT",
    "externs should be avoided in .c files": "AVOID_EXTERNS",
    "simple_strtoul is obsolete, use kstrtoul instead": "CONSIDER_KSTRTO",
    "simple_strtol is obsolete, use kstrtol instead": "CONSIDER_KSTRTO",
    "Prefer using": "USE_FUNC",  # "Prefer using '\"%%s...\", __func__'"
    "else is not generally useful after a break or return": "UNNECESSARY_ELSE",
    "Prefer __weak over __attribute__((weak))": "WEAK_DECLARATION",
    "Possible unnecessary 'out of memory' message": "OOM_MESSAGE",
    "__initdata should be placed after": "MISPLACED_INIT",
    "msleep < 20ms can sleep for up to 20ms": "MSLEEP",
    "Prefer strscpy over strcpy": "STRCPY",
    "Prefer using strscpy instead of strncpy": "STRNCPY",
    "switch and case should be at the same indent": "SWITCH_CASE_INDENT_LEVEL",
    "Avoid logging continuation uses where feasible": "LOGGING_CONTINUATION",
    "It's generally not useful to have the filename in the file": "EMBEDDED_FILENAME",
    "please, no spaces at the start of a line": "LEADING_SPACE",
}

# Mapeo de patrones para printk
PRINTK_PATTERNS = {
    r"Prefer.*printk\(KERN_INFO": "PREFER_PR_LEVEL",
    r"Prefer.*printk\(KERN_ERR": "PREFER_PR_LEVEL",
    r"Prefer.*printk\(KERN_WARNING": "PREFER_PR_LEVEL",
    r"Prefer.*printk\(KERN_DEBUG": "PREFER_PR_LEVEL",
    r"Prefer.*printk\(KERN_EMERG": "PREFER_PR_LEVEL",
    r"Prefer.*printk\(KERN_NOTICE": "PREFER_PR_LEVEL",
    r"printk\(\) should include KERN": "PRINTK_WITHOUT_KERN_LEVEL",
    r"Comparing jiffies": "JIFFIES_COMPARISON",
    r"Symbolic permissions.*are not preferred": "SYMBOLIC_PERMS",
    r"Use #include <linux/.+> instead of <asm/.+>": "ARCH_INCLUDE_LINUX",
    r"Missing or malformed SPDX": "SPDX_LICENSE_TAG",
    r"Improper SPDX comment style": "SPDX_LICENSE_TAG",
}

def extract_type_from_message(message):
    """Extrae el tipo de checkpatch de un mensaje"""
    # Limpiar el mensaje
    clean_msg = message.replace("ERROR:", "").replace("WARNING:", "").strip()
    
    # Buscar coincidencias exactas primero
    for pattern, msg_type in MESSAGE_TO_TYPE.items():
        if pattern in clean_msg:
            return msg_type
    
    # Buscar patrones con regex
    for pattern, msg_type in PRINTK_PATTERNS.items():
        if re.search(pattern, clean_msg):
            return msg_type
    
    return None

def analyze_json():
    """Analiza el JSON actual para ver qué tipos de checkpatch aparecen"""
    with open('json/checkpatch.json') as f:
        data = json.load(f)
    
    # Contadores
    error_msgs = defaultdict(int)
    warning_msgs = defaultdict(int)
    error_types = defaultdict(int)
    warning_types = defaultdict(int)
    unknown_messages = set()
    
    for item in data:
        for issue in item.get('error', []):
            msg = issue['message']
            error_msgs[msg] += 1
            msg_type = extract_type_from_message(msg)
            if msg_type:
                error_types[msg_type] += 1
            else:
                unknown_messages.add(('ERROR', msg))
        
        for issue in item.get('warning', []):
            msg = issue['message']
            warning_msgs[msg] += 1
            msg_type = extract_type_from_message(msg)
            if msg_type:
                warning_types[msg_type] += 1
            else:
                unknown_messages.add(('WARNING', msg))
    
    return {
        'error_msgs': error_msgs,
        'warning_msgs': warning_msgs,
        'error_types': error_types,
        'warning_types': warning_types,
        'unknown': unknown_messages
    }

def analyze_coverage():
    """Analiza la cobertura de tipos basándose en el JSON real"""
    
    # Analizar JSON actual
    json_data = analyze_json()
    
    # Extraer tipos que tenemos implementados
    implemented_types = set()
    for msg_key in AUTO_FIX_RULES.keys():
        msg_type = extract_type_from_message(msg_key)
        if msg_type:
            implemented_types.add(msg_type)
    
    # Extraer tipos que aparecen en el análisis
    found_error_types = set(json_data['error_types'].keys())
    found_warning_types = set(json_data['warning_types'].keys())
    
    print("\n" + "="*80)
    print("ANÁLISIS DE COBERTURA REAL (basado en json/checkpatch.json)")
    print("="*80)
    
    # Errores
    print(f"\n📊 ERRORES ENCONTRADOS: {sum(json_data['error_types'].values())} casos, {len(found_error_types)} tipos únicos")
    print("-" * 80)
    covered_errors = found_error_types & implemented_types
    uncovered_errors = found_error_types - implemented_types
    
    if covered_errors:
        print(f"\n✅ TIPOS CON FIX IMPLEMENTADO ({len(covered_errors)}):")
        for t in sorted(covered_errors):
            count = json_data['error_types'][t]
            print(f"  - {t}: {count} casos")
    
    if uncovered_errors:
        print(f"\n❌ TIPOS SIN FIX IMPLEMENTADO ({len(uncovered_errors)}):")
        for t in sorted(uncovered_errors):
            count = json_data['error_types'][t]
            print(f"  - {t}: {count} casos")
    
    # Warnings
    print(f"\n📊 WARNINGS ENCONTRADOS: {sum(json_data['warning_types'].values())} casos, {len(found_warning_types)} tipos únicos")
    print("-" * 80)
    covered_warnings = found_warning_types & implemented_types
    uncovered_warnings = found_warning_types - implemented_types
    
    if covered_warnings:
        print(f"\n✅ TIPOS CON FIX IMPLEMENTADO ({len(covered_warnings)}):")
        for t in sorted(covered_warnings):
            count = json_data['warning_types'][t]
            print(f"  - {t}: {count} casos")
    
    if uncovered_warnings:
        print(f"\n❌ TIPOS SIN FIX IMPLEMENTADO ({len(uncovered_warnings)}):")
        for t in sorted(uncovered_warnings):
            count = json_data['warning_types'][t]
            print(f"  - {t}: {count} casos")
    
    # Mensajes desconocidos
    if json_data['unknown']:
        print(f"\n⚠️  MENSAJES SIN MAPEAR A TIPO ({len(json_data['unknown'])}):")
        print("-" * 80)
        for severity, msg in sorted(json_data['unknown']):
            print(f"  [{severity}] {msg}")
    
    # Resumen
    total_found = len(found_error_types) + len(found_warning_types)
    total_covered = len(covered_errors) + len(covered_warnings)
    pct = (total_covered / total_found * 100) if total_found else 0
    
    print("\n" + "="*80)
    print(f"RESUMEN: {total_covered}/{total_found} tipos cubiertos ({pct:.1f}%)")
    print(f"  - Errores: {len(covered_errors)}/{len(found_error_types)}")
    print(f"  - Warnings: {len(covered_warnings)}/{len(found_warning_types)}")
    print(f"  - Total fixes implementados: {len(implemented_types)}")
    print("="*80)

if __name__ == "__main__":
    analyze_coverage()
